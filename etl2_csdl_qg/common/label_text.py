"""
label_text.py — Lấy văn bản từ cây mục nhãn (label_section.jsonl) cho 7 cột văn bản (cột 15-21).

Mỗi cột lấy các mục theo mã LOINC (vd 34067-9 = Indications and Usage). Mã đứng sau
trong danh sách là dự phòng khi không có mã đứng trước.
"""

import re


# ---------------------------------------------------------------- đọc một nút mục nhãn

# Danh sách mục con của một mục (không có thì là danh sách rỗng).
def children_of(node):
    children = node.get("children")
    if not children:
        return []
    return children


# Tiêu đề của một mục, đã bỏ khoảng trắng hai đầu (không có thì là "").
def title_of(node):
    title = node.get("title")
    if not title:
        return ""
    return title.strip()


# Tiêu đề gốc của một mục, chưa bỏ khoảng trắng (không có thì là "").
def title_of_raw(node):
    title = node.get("title")
    if not title:
        return ""
    return title


# Văn bản đầy đủ của một mục: văn bản của chính nó + văn bản các mục con.
# Văn bản mục cha không chứa văn bản mục con, nên phải nối thêm; mục con có tiêu đề
# thì đặt tiêu đề lên trước (nếu văn bản chưa bắt đầu bằng tiêu đề đó).
def section_text(node):
    parts = []

    # văn bản của chính mục
    if node.get("text"):
        parts.append(node["text"].strip())

    # văn bản các mục con, kèm tiêu đề
    for child in children_of(node):
        child_text = section_text(child)
        title = title_of(child)

        if title and child_text and not child_text.startswith(title):
            child_text = title + "\n" + child_text
        elif title and not child_text:
            child_text = title

        if child_text:
            parts.append(child_text)

    # bỏ phần rỗng rồi nối bằng xuống dòng
    non_empty = []
    for part in parts:
        if part:
            non_empty.append(part)

    return "\n".join(non_empty)


# ---------------------------------------------------------------- tìm mục

# Mọi mục có mã LOINC này, theo thứ tự trong tài liệu.
# Đã lấy một mục thì không tìm tiếp bên trong nó (văn bản mục cha đã gồm mục con).
def sections_by_code(sections, loinc_code):
    result = []

    for node in sections:
        if node.get("loinc_code") == loinc_code:
            result.append(node)
        else:
            result.extend(sections_by_code(children_of(node), loinc_code))

    return result


# Mục đầu tiên (tìm cả mục con) có tiêu đề khớp biểu thức pattern, không phân biệt hoa thường.
def first_section_by_title(sections, pattern):
    for node in sections:
        if re.search(pattern, title_of_raw(node), re.I):
            return node

        found = first_section_by_title(children_of(node), pattern)
        if found is not None:
            return found

    return None


# Tập id của mọi mục con cháu bên trong một mục.
def descendant_ids(node):
    result = set()

    for child in children_of(node):
        result.add(child["id"])
        result.update(descendant_ids(child))

    return result


# Bỏ các mục nằm bên trong một mục khác của danh sách; giữ thứ tự.
def outermost_sections(nodes):
    inside = set()
    for node in nodes:
        inside.update(descendant_ids(node))

    result = []
    for node in nodes:
        if node["id"] not in inside:
            result.append(node)

    return result


# Văn bản của từng mục trong danh sách, bỏ mục không có chữ.
def texts_of(nodes):
    result = []

    for node in nodes:
        text = section_text(node)
        if text:
            result.append(text)

    return result


# ---------------------------------------------------------------- chọn và nối đoạn văn

# Các đoạn văn có nhắc tên thuốc (name hoặc generic_name), không phân biệt hoa thường.
def passages_mentioning_drug(passages, drug):
    names = []
    if drug["name"]:
        names.append(drug["name"].lower())
    if drug["generic_name"]:
        names.append(drug["generic_name"].lower())

    result = []
    for passage in passages:
        lower = passage.lower()
        for name in names:
            if name in lower:
                result.append(passage)
                break

    return result


# Chọn nhóm đoạn văn dùng cho cột. groups = đoạn văn của mã chính, rồi các mã dự phòng.
# Tài liệu bộ kit có một nhãn con cho mỗi thành phần: ưu tiên nhóm đầu tiên có đoạn
# nhắc tên thuốc. Còn lại lấy nhóm đầu tiên khác rỗng.
def choose_passages(groups, drug, in_kit_document):
    if in_kit_document:
        for group in groups:
            mentioning = passages_mentioning_drug(group, drug)
            if mentioning:
                return mentioning

    for group in groups:
        if group:
            return group

    return []


# Nối các đoạn văn bằng một dòng trống; bỏ đoạn trùng (giữ lần xuất hiện đầu).
def join_passages(passages):
    seen = set()
    kept = []

    for passage in passages:
        key = passage.strip()
        if key not in seen:
            seen.add(key)
            kept.append(passage)

    return "\n\n".join(kept)


# ---------------------------------------------------------------- theo thuốc

# Dòng label_document của tài liệu chứa thuốc.
def document_of(data, drug):
    return data.documents[drug["document_id"]]


# Cây mục nhãn của tài liệu chứa thuốc (không có thì là danh sách rỗng).
def sections_of(data, drug):
    return data.sections.get(drug["document_id"], [])


# Thuốc có nằm trong tài liệu bộ kit không.
def is_kit(data, drug):
    return drug["document_id"] in data.kit_documents


# Văn bản (khác rỗng) của mọi mục có mã LOINC này trong tài liệu chứa thuốc.
# Nhiều thuốc chung một tài liệu, nên kết quả được tính một lần rồi lưu vào data.cache.
def texts_for_code(data, drug, loinc_code):
    key = (drug["document_id"], loinc_code)

    if key not in data.cache:
        nodes = sections_by_code(sections_of(data, drug), loinc_code)
        data.cache[key] = texts_of(nodes)

    return data.cache[key]


# Văn bản của cột theo danh sách mã LOINC (mã sau là dự phòng cho mã trước).
def text_for_codes(data, drug, loinc_codes):
    groups = []
    for code in loinc_codes:
        groups.append(texts_for_code(data, drug, code))

    passages = choose_passages(groups, drug, is_kit(data, drug))
    return join_passages(passages)
