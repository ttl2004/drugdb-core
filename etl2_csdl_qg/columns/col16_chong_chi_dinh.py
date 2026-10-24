from etl2_csdl_qg.common.label_text import text_for_codes

HEADER = "Chống chỉ định"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []
    for drug in data.drugs:
        values.append(text_for_codes(data, drug, ["34070-3", "50570-1"]))
    return values
