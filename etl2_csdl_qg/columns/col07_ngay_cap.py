"""
Cột 7 — Ngày cấp số giấy phép lưu hành: ngày bắt đầu lưu hành, dạng ngày/tháng/năm.
"""

from etl2_csdl_qg.common.formatting import format_date

HEADER = "Ngày cấp số giấy phép lưu hành\n(Định dạng ngày-tháng-năm)"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []
    for drug in data.drugs:
        values.append(format_date(drug["marketing_start"]))
    return values
