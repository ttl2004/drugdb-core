"""
Cột 16 — Chống chỉ định: mục Contraindications (LOINC 34070-3). Tiếng Anh.
Thuốc OTC không có mục này thì lấy mục "Do not use" (LOINC 50570-1).
"""

from etl2_csdl_qg.common.label_text import text_for_codes

HEADER = "Chống chỉ định"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []
    for drug in data.drugs:
        values.append(text_for_codes(data, drug, ["34070-3", "50570-1"]))
    return values
