"""
Cột 21 — Liều lượng: mục Dosage and Administration (LOINC 34068-7). Tiếng Anh.
"""

from etl2_csdl_qg.common.label_text import text_for_codes

HEADER = "Liều lượng"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []
    for drug in data.drugs:
        values.append(text_for_codes(data, drug, ["34068-7"]))
    return values
