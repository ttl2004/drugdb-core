"""
Cột 2 — Mã định danh thuốc: mã NDC của thuốc.
"""

HEADER = "Mã định danh thuốc (*)"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []
    for drug in data.drugs:
        values.append(drug["ndc"])
    return values
