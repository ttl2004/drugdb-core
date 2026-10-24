"""
Cột 8 — Ngày hết hiệu lực lưu hành: ngày kết thúc lưu hành, dạng ngày/tháng/năm.
"""

from etl2_csdl_qg.common.formatting import format_date

HEADER = "Ngày hết hiệu lực lưu hành\n(Định dạng ngày-tháng-năm)"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []
    for drug in data.drugs:
        values.append(format_date(drug["marketing_end"]))
    return values
