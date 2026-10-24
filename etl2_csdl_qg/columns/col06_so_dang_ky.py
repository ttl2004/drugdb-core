"""
Cột 6 — Số đăng ký lưu hành: số hồ sơ phê duyệt (vd NDA020702, ANDA076543).
"""

HEADER = "Số đăng ký lưu hành (*)"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []
    for drug in data.drugs:
        values.append(drug["approval_id"])
    return values
