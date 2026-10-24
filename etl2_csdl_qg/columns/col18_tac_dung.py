"""
Cột 18 — Tác dụng. Tiếng Anh.
Thuốc OTC: mục Purpose (LOINC 55105-1).
Thuốc kê đơn: Mechanism of Action (LOINC 43679-0), dự phòng Clinical Pharmacology (LOINC 34090-1).
"""

from etl2_csdl_qg.common.label_text import document_of, text_for_codes

HEADER = "Tác dụng"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []

    for drug in data.drugs:
        if "OTC" in document_of(data, drug)["doc_code_display"]:
            values.append(text_for_codes(data, drug, ["55105-1"]))
        else:
            values.append(text_for_codes(data, drug, ["43679-0", "34090-1"]))

    return values
