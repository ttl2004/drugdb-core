"""
Cột 13 — Đường dùng, tra từ điển duong_dung (vd ORAL -> Uống).
Chưa có trong từ điển thì giữ tiếng Anh, viết hoa chữ đầu.
"""

from etl2_csdl_qg.constants import ROUTE_NOT_APPLICABLE

HEADER = "Đường dùng"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs. Không có đường dùng thì để trống.
def build(data):
    values = []

    for drug in data.drugs:
        route = drug["route_name"]

        if route == "" or route == ROUTE_NOT_APPLICABLE:
            values.append("")
            continue

        vietnamese = data.dictionary.lookup("duong_dung", route, drug["id"])
        if vietnamese is None:
            values.append(route.capitalize())
        else:
            values.append(vietnamese)

    return values
