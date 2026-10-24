"""
Cột 11 — Nước sản xuất. XML DailyMed không có địa chỉ nhà sản xuất, nên ghi "US" cho mọi thuốc.
"""

from etl2_csdl_qg.constants import COUNTRY

HEADER = "Nước sản xuất (*)"


# Giá trị cột cho mọi thuốc: đều là COUNTRY.
def build(data):
    values = []
    for drug in data.drugs:
        values.append(COUNTRY)
    return values
