import re

from etl2_csdl_qg.columns import col09_ham_luong

# Header của file mẫu có một dấu cách ở cuối, giữ nguyên
HEADER = "Tên thuốc (*) "


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
# Chỉ nối hàm lượng khi tên đó có nhiều hàm lượng khác nhau và tên chưa có chữ số.
def build(data):
    # tên gốc của từng thuốc
    names = []
    for drug in data.drugs:
        if drug["name"]:
            names.append(drug["name"])
        else:
            names.append(drug["generic_name"])

    # các hàm lượng khác nhau của mỗi tên
    strengths = col09_ham_luong.build(data)
    strengths_by_name = {}
    for i in range(len(names)):
        if names[i] not in strengths_by_name:
            strengths_by_name[names[i]] = set()
        strengths_by_name[names[i]].add(strengths[i])

    # nối hàm lượng cho tên bị trùng
    values = []
    for i in range(len(names)):
        name = names[i]
        strength = strengths[i]
        has_many_strengths = len(strengths_by_name[name]) > 1
        has_digit = re.search(r"\d", name) is not None

        if name and has_many_strengths and strength and not has_digit:
            values.append(name + " " + strength)
        else:
            values.append(name)

    return values
