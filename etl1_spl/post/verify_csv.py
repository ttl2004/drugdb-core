import csv
import os
from collections import Counter

# Một số mục nhãn có text_xml dài hơn giới hạn mặc định 128 KB của module csv
csv.field_size_limit(1 << 30)

# Số dòng kỳ vọng khi chạy TOÀN BỘ dữ liệu, lấy từ tài liệu thiết kế
EXPECTED = {
    "label_document.csv": 3734,
    "drug_knowledge.csv": 5226,      # 5.019 manufacturedProduct + 207 partProduct có NDC riêng
    "drug_ingredient.csv": 49803,
    "label_section.csv": 114808,
}


# Đọc cả file CSV thành danh sách dict (mỗi dòng một dict).
def read(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# Lấy tập giá trị (không trùng) của một cột; skip_empty=True thì bỏ ô rỗng.
def values_of(rows, column, skip_empty):
    result = set()
    for row in rows:
        value = row[column]
        if skip_empty and not value:
            continue
        result.add(value)
    return result


# Đếm số dòng có cột column bằng value.
def count_where(rows, column, value):
    n = 0
    for row in rows:
        if row[column] == value:
            n += 1
    return n


# Đếm số dòng có cột column khác rỗng.
def count_filled(rows, column):
    n = 0
    for row in rows:
        if row[column]:
            n += 1
    return n


# Báo lỗi nếu cột khoá chính có giá trị trùng.
def check_unique(rows, column, table, problems):
    unique = values_of(rows, column, False)
    if len(unique) != len(rows):
        problems.append("%s.%s TRÙNG: %d" % (table, column, len(rows) - len(unique)))
    return unique


# Báo lỗi nếu cột khoá ngoại có giá trị không tồn tại trong bảng được trỏ tới.
# nullable=True: cột được phép rỗng, bỏ qua ô rỗng; ngược lại ô rỗng cũng tính là mồ côi.
def check_foreign_key(rows, column, targets, table, problems, nullable=False):
    orphans = values_of(rows, column, nullable) - targets
    if orphans:
        problems.append("%s.%s mồ côi: %d" % (table, column, len(orphans)))


# Báo lỗi nếu cặp (col_a, col_b) bị trùng giữa các dòng.
def check_pair_unique(rows, col_a, col_b, table, problems):
    pairs = Counter()
    for row in rows:
        pairs[(row[col_a], row[col_b])] += 1

    duplicates = 0
    for count in pairs.values():
        if count > 1:
            duplicates += 1

    if duplicates:
        problems.append("%s (%s, %s) TRÙNG: %d" % (table, col_a, col_b, duplicates))


# Báo lỗi nếu display_order của các thành phần trong một thuốc không chạy liên tục 1..n.
def check_display_order(rows, problems):
    orders = {}
    for row in rows:
        orders.setdefault(row["drug_id"], []).append(int(row["display_order"]))

    bad = 0
    for numbers in orders.values():
        if sorted(numbers) != list(range(1, len(numbers) + 1)):
            bad += 1

    if bad:
        problems.append("drug_ingredient.display_order không liên tục: %d thuốc" % bad)


# Kiểm tra các CSV trong folder.
# expect_full=True (chạy toàn bộ dữ liệu) thì so thêm số dòng với tài liệu thiết kế.
# Trả về {"ok": bool, "problems": [...], "notes": [...]}.
def run(folder, expect_full, log):
    problems = []
    notes = []

    # tài liệu
    docs = read(os.path.join(folder, "label_document.csv"))
    log("  label_document            : %6d dòng" % len(docs))
    doc_ids = check_unique(docs, "id", "label_document", problems)
    check_pair_unique(docs, "set_id", "version", "label_document", problems)
    notes.append("title rỗng: %d" % count_where(docs, "title", ""))

    # tổ chức
    orgs = read(os.path.join(folder, "organization.csv"))
    log("  organization              : %6d dòng" % len(orgs))
    org_ids = check_unique(orgs, "id", "organization", problems)
    check_foreign_key(docs, "labeler_id", org_ids, "label_document", problems, nullable=True)

    # thuốc
    drugs = read(os.path.join(folder, "drug_knowledge.csv"))
    log("  drug_knowledge            : %6d dòng" % len(drugs))
    drug_ids = check_unique(drugs, "id", "drug_knowledge", problems)
    check_foreign_key(drugs, "document_id", doc_ids, "drug_knowledge", problems)
    check_foreign_key(drugs, "manufacturer_id", org_ids, "drug_knowledge", problems, nullable=True)
    check_pair_unique(drugs, "document_id", "ndc", "drug_knowledge", problems)
    notes.append("không có hoạt chất: %d" % count_where(drugs, "has_active", "0"))

    # thuốc dùng cho người = tài liệu không thuộc nhóm animal
    human_docs = set()
    for row in docs:
        if row["source_category"] != "animal":
            human_docs.add(row["id"])
    human_drugs = 0
    for row in drugs:
        if row["document_id"] in human_docs:
            human_drugs += 1
    notes.append("thuốc người (source_category != animal): %d" % human_drugs)

    # chất
    ings = read(os.path.join(folder, "ingredient.csv"))
    log("  ingredient                : %6d dòng" % len(ings))
    uniis = check_unique(ings, "unii", "ingredient", problems)
    outside = values_of(ings, "parent_unii", True) - uniis
    if outside:
        notes.append("parent_unii trỏ ra ngoài tập: %d" % len(outside))

    # thuốc – chất
    dis = read(os.path.join(folder, "drug_ingredient.csv"))
    log("  drug_ingredient           : %6d dòng" % len(dis))
    check_unique(dis, "id", "drug_ingredient", problems)
    check_foreign_key(dis, "drug_id", drug_ids, "drug_ingredient", problems)
    check_foreign_key(dis, "ingredient_unii", uniis, "drug_ingredient", problems)
    check_display_order(dis, problems)
    class_counts = Counter()
    for row in dis:
        class_counts[row["class_code"]] += 1
    notes.append("class_code: %s" % dict(class_counts))
    notes.append("có hàm lượng: %d" % count_filled(dis, "strength_value"))

    # bộ combo
    part_path = os.path.join(folder, "drug_part.csv")
    if os.path.exists(part_path):
        parts = read(part_path)
        log("  drug_part                 : %6d dòng" % len(parts))
        check_unique(parts, "id", "drug_part", problems)
        check_foreign_key(parts, "parent_drug_id", drug_ids, "drug_part", problems)
        check_foreign_key(parts, "part_drug_id", drug_ids, "drug_part", problems)
        pairs = set()
        for row in parts:
            pairs.add((row["parent_drug_id"], row["part_drug_id"]))
        notes.append("cặp combo khác nhau: %d" % len(pairs))

    # cây mục nhãn
    secs = read(os.path.join(folder, "label_section.csv"))
    log("  label_section             : %6d dòng" % len(secs))
    sec_ids = check_unique(secs, "id", "label_section", problems)
    check_foreign_key(secs, "parent_id", sec_ids, "label_section", problems, nullable=True)
    check_foreign_key(secs, "document_id", doc_ids, "label_section", problems)
    notes.append("có text_xml: %d" % count_filled(secs, "text_xml"))
    notes.append("có text_plain: %d" % count_filled(secs, "text_plain"))
    depths = Counter()
    for row in secs:
        depths[int(row["depth"])] += 1
    notes.append("độ sâu: %s" % dict(sorted(depths.items())))

    # cây bao bì
    pkgs = read(os.path.join(folder, "drug_package.csv"))
    log("  drug_package              : %6d dòng" % len(pkgs))
    pkg_ids = check_unique(pkgs, "id", "drug_package", problems)
    check_foreign_key(pkgs, "parent_id", pkg_ids, "drug_package", problems, nullable=True)
    check_foreign_key(pkgs, "drug_id", drug_ids, "drug_package", problems)
    notes.append("nút không có NDC: %d" % count_where(pkgs, "ndc", ""))

    # chỉ mục DSV
    for name in ["spl_document_index.csv", "spl_document_delta.csv"]:
        path = os.path.join(folder, name)
        if not os.path.exists(path):
            continue
        rows = read(path)
        log("  %-25s : %6d dòng" % (name.replace(".csv", ""), len(rows)))
        check_unique(rows, "set_id", name.replace(".csv", ""), problems)

    # so số dòng với tài liệu thiết kế (chỉ khi chạy toàn bộ)
    if expect_full:
        actual = {
            "label_document.csv": len(docs),
            "drug_knowledge.csv": len(drugs),
            "drug_ingredient.csv": len(dis),
            "label_section.csv": len(secs),
        }
        log("  --- đối chiếu tài liệu thiết kế ---")
        for name in EXPECTED:
            expected = EXPECTED[name]
            got = actual[name]
            mark = "OK "
            if got != expected:
                mark = "LỆCH"
                problems.append("%s lệch: kỳ vọng %d, thực tế %d" % (name, expected, got))
            log("    %-26s kỳ vọng %7d  thực tế %7d  %s" % (name, expected, got, mark))

    # in kết quả
    log("  --- ghi chú ---")
    for note in notes:
        log("    " + note)

    log("  --- kết luận ---")
    for problem in problems:
        log("    ✗ " + problem)
    if not problems:
        log("    ✓ Không phát hiện vấn đề toàn vẹn")

    return {"ok": len(problems) == 0, "problems": problems, "notes": notes}
