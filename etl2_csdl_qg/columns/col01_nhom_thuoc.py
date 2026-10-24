"""
Cột 1 — Nhóm thuốc: Vắc xin / Sinh phẩm / Nguyên liệu làm thuốc / Dược liệu / Hóa dược.
"""

HEADER = "Nhóm thuốc (*)"


# Xếp nhóm một thuốc theo loại tài liệu, theo thứ tự ưu tiên:
# vắc xin -> sinh phẩm (dẫn xuất huyết tương hoặc phê duyệt BLA) -> nguyên liệu
# -> dược liệu (nhóm homeopathic) -> còn lại là hóa dược.
def group_of(data, drug):
    doc = data.documents[drug["document_id"]]
    doc_type = doc["doc_code_display"]

    if doc_type == "VACCINE LABEL":
        return "Vắc xin"

    if doc_type == "PLASMA DERIVATIVE" or drug["approval_code"].upper() == "BLA":
        return "Sinh phẩm"

    if doc_type.startswith("BULK INGREDIENT"):
        return "Nguyên liệu làm thuốc"

    if doc["source_category"] == "homeopathic":
        return "Dược liệu"

    return "Hóa dược"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []
    for drug in data.drugs:
        values.append(group_of(data, drug))
    return values
