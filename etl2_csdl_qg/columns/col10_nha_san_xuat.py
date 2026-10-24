"""
Cột 10 — Nhà sản xuất: tổ chức ở tầng sâu nhất trong cây tác giả của nhãn (do ETL 1 chọn).
"""

HEADER = "Nhà sản xuất"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []
    for drug in data.drugs:
        values.append(drug["manufacturer_name"])
    return values
