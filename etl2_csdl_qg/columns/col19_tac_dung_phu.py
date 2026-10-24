"""
Cột 19 — Tác dụng phụ: mục Adverse Reactions (LOINC 34084-4). Tiếng Anh.
"""

from etl2_csdl_qg.common.label_text import text_for_codes

HEADER = "Tác dụng phụ"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []
    for drug in data.drugs:
        values.append(text_for_codes(data, drug, ["34084-4"]))
    return values
