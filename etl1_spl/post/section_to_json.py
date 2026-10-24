import csv
import json
import os
import time

# Một số mục nhãn có text_xml dài hơn giới hạn mặc định 128 KB của module csv
csv.field_size_limit(1 << 30)


# Chuỗi rỗng đổi thành None (ra null trong JSON).
def empty_to_none(value):
    if value:
        return value
    return None


# Tạo một nút mục nhãn (chưa có mục con) từ một dòng CSV.
def build_node(row, with_xml, with_plain):
    node = {
        "id": int(row["id"]),
        "anchor": empty_to_none(row["anchor"]),
        "section_uuid": empty_to_none(row["section_uuid"]),
        "loinc_code": empty_to_none(row["loinc_code"]),
        "loinc_display": empty_to_none(row["loinc_display"]),
        "title": empty_to_none(row["title"]),
        "seq": int(row["seq"]),
        "depth": int(row["depth"]),
    }

    if with_plain:
        node["text"] = empty_to_none(row["text_plain"])
    if with_xml:
        node["text_xml"] = empty_to_none(row["text_xml"])

    node["children"] = []
    return node


# Dựng cây mục nhãn từ các dòng CSV của MỘT tài liệu.
# Trả về danh sách mục gốc; mục con nằm trong "children" theo đúng thứ tự trong CSV.
def build_tree(rows, with_xml, with_plain):
    # tạo trước mọi nút, tra theo id
    nodes = {}
    for row in rows:
        nodes[int(row["id"])] = build_node(row, with_xml, with_plain)

    # gắn từng nút vào mục cha của nó
    roots = []
    for row in rows:
        node = nodes[int(row["id"])]
        parent_id = row["parent_id"]

        if not parent_id:
            roots.append(node)
            continue

        parent = nodes.get(int(parent_id))
        if parent is None:
            # mục cha không thuộc tài liệu này (không xảy ra với dữ liệu hiện có): đưa lên gốc
            roots.append(node)
        else:
            parent["children"].append(node)

    return roots


# Đọc label_document.csv thành dict {document_id: dòng}, để lấy thông tin tài liệu.
def read_documents(doc_path):
    docs = {}
    with open(doc_path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            docs[row["id"]] = row
    return docs


# Tạo chuỗi JSON (một dòng) cho một tài liệu và cây mục nhãn của nó.
def document_json(doc_id, rows, docs, with_xml, with_plain, pretty):
    info = docs.get(doc_id, {})

    version = None
    if info.get("version"):
        version = int(info["version"])

    data = {
        "document_id": doc_id,
        "set_id": empty_to_none(info.get("set_id")),
        "version": version,
        "title": empty_to_none(info.get("title")),
        "effective_time": empty_to_none(info.get("effective_time")),
        "doc_code": empty_to_none(info.get("doc_code")),
        "doc_code_display": empty_to_none(info.get("doc_code_display")),
        "source_category": empty_to_none(info.get("source_category")),
        "section_count": len(rows),
        "sections": build_tree(rows, with_xml, with_plain),
    }

    # pretty: thụt lề cho dễ đọc; mặc định viết gọn nhất
    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=1)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


# Đếm số mục nhãn ở mỗi độ sâu trong file JSONL (duyệt cây bằng ngăn xếp).
def count_depths_json(out_path):
    counts = {}

    with open(out_path, "r", encoding="utf-8") as f:
        for line in f:
            stack = []
            for node in json.loads(line)["sections"]:
                stack.append((node, 1))

            while stack:
                node, depth = stack.pop()
                counts[depth] = counts.get(depth, 0) + 1
                for child in node["children"]:
                    stack.append((child, depth + 1))

    return counts


# Đối chiếu file JSONL với CSV để chắc chắn không mất dữ liệu:
# số tài liệu, số mục nhãn, số mục ở mỗi độ sâu. Trả về True nếu khớp hết.
def check_against_csv(sec_path, out_path, n_docs, n_sections, log):
    with open(sec_path, "r", encoding="utf-8-sig", newline="") as f:
        csv_rows = list(csv.DictReader(f))

    # số tài liệu có mục nhãn trong CSV
    csv_docs = set()
    for row in csv_rows:
        csv_docs.add(row["document_id"])

    if n_docs != len(csv_docs):
        log("  ✗ số tài liệu lệch: CSV %d, JSONL %d" % (len(csv_docs), n_docs))
        return False
    log("  ✓ số tài liệu khớp (%d)" % n_docs)

    if n_sections != len(csv_rows):
        log("  ✗ số mục nhãn lệch: CSV %d, JSONL %d" % (len(csv_rows), n_sections))
        return False
    log("  ✓ số mục nhãn khớp (%d)" % n_sections)

    # số mục ở mỗi độ sâu theo cột depth của CSV
    depth_csv = {}
    for row in csv_rows:
        depth = int(row["depth"])
        depth_csv[depth] = depth_csv.get(depth, 0) + 1

    depth_json = count_depths_json(out_path)

    if depth_json != depth_csv:
        log("  ✗ phân bố độ sâu LỆCH: CSV %s, JSON %s"
            % (dict(sorted(depth_csv.items())), dict(sorted(depth_json.items()))))
        return False
    log("  ✓ phân bố độ sâu khớp: %s" % dict(sorted(depth_json.items())))
    return True


# Ghi label_section.jsonl (label_section_noXml.jsonl nếu bỏ text_xml) trong thư mục folder,
# rồi đối chiếu ngược với CSV. Trả về dict tổng kết, khoá "ok" cho biết đối chiếu có khớp không.
def run(folder, with_xml, with_plain, pretty, log):
    sec_path = os.path.join(folder, "label_section.csv")
    doc_path = os.path.join(folder, "label_document.csv")

    out_path = os.path.join(folder, "label_section.jsonl")
    if not with_xml:
        out_path = os.path.join(folder, "label_section_noXml.jsonl")

    log("  Đọc %s" % doc_path)
    docs = read_documents(doc_path)
    log("    %d tài liệu" % len(docs))

    log("  Đọc %s" % sec_path)
    started = time.time()
    n_docs = 0
    n_sections = 0

    with open(sec_path, "r", encoding="utf-8-sig", newline="") as fin, \
            open(out_path, "w", encoding="utf-8", newline="\n") as fout:

        # CSV đã xếp các mục của cùng tài liệu liền nhau: gom đến khi đổi tài liệu thì ghi
        current_doc = None
        buffer = []

        for row in csv.DictReader(fin):
            if row["document_id"] != current_doc and current_doc is not None:
                fout.write(document_json(current_doc, buffer, docs, with_xml, with_plain, pretty) + "\n")
                n_docs += 1
                n_sections += len(buffer)
                buffer = []

            current_doc = row["document_id"]
            buffer.append(row)

        # ghi tài liệu cuối cùng
        if current_doc is not None:
            fout.write(document_json(current_doc, buffer, docs, with_xml, with_plain, pretty) + "\n")
            n_docs += 1
            n_sections += len(buffer)

    size = os.path.getsize(out_path)
    log("  Đã ghi %s" % out_path)
    log("    tài liệu: %d, mục nhãn: %d, %.1f MB, %.0f giây"
        % (n_docs, n_sections, size / 1048576, time.time() - started))

    ok = check_against_csv(sec_path, out_path, n_docs, n_sections, log)

    return {
        "file": os.path.basename(out_path),
        "documents": n_docs,
        "sections": n_sections,
        "bytes": size,
        "ok": ok,
    }
