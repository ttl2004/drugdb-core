"""
Cột 4 — Loại kiểm soát đặc biệt. Tạm để trống: chưa chốt cách phân loại
(xem mục "Cột 4" trong tài liệu mapping).
"""

HEADER = "Loại kiểm soát đặc biệt (*)"


# Giá trị cột cho mọi thuốc: tạm thời đều rỗng.
def build(data):
    values = []
    for drug in data.drugs:
        values.append("")
    return values
