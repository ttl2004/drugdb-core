"""
Cột 15 — Chỉ định: mục Indications and Usage (LOINC 34067-9). Tiếng Anh.
"""

from etl2_csdl_qg.common.label_text import text_for_codes

HEADER = "Chỉ định"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []
    for drug in data.drugs:
        values.append(text_for_codes(data, drug, ["34067-9"]))
    return values
