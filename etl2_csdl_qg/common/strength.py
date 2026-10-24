"""
strength.py — Tên và hàm lượng hoạt chất của thuốc (dùng cho cột 3, 9, 14).
"""

from etl2_csdl_qg.common.formatting import format_number


# Đổi mã đơn vị (UCUM) sang chữ hiển thị bằng từ điển don_vi; chưa có thì giữ mã gốc.
def unit_text(data, code, drug_id):
    vietnamese = data.dictionary.lookup("don_vi", code, drug_id)

    if vietnamese is None:
        return code
    return vietnamese


# Ghép hàm lượng của một dòng drug_ingredient: tử số + đơn vị, rồi "/ mẫu số + đơn vị".
# Ví dụ: "500mg", "10mg/mL", "5mg/5mL", "4g/100". Không có hàm lượng thì trả về "".
def strength_text(data, row):
    value = row["strength_value"]
    unit = row["strength_unit"]
    if not value:
        return ""

    # tử số (đơn vị "1" nghĩa là không có đơn vị)
    result = format_number(value)
    if unit != "" and unit != "1":
        result = result + unit_text(data, unit, row["drug_id"])

    # mẫu số; mẫu số bằng 1 thì không ghi số
    basis_unit = row["basis_unit"]
    basis_value = format_number(row["basis_value"])
    if basis_value == "1":
        basis_value = ""

    if basis_unit == "1":
        # mẫu số không đơn vị, vd "4g/100"
        if basis_value != "":
            result = result + "/" + basis_value
    elif basis_unit:
        result = result + "/" + basis_value + unit_text(data, basis_unit, row["drug_id"])

    return result


# Các hoạt chất của thuốc theo display_order: danh sách {"name": tên, "strength": hàm lượng}.
# Chất không có tên thì dùng mã UNII.
def active_ingredients(data, drug):
    result = []

    for row in data.active_ingredients.get(drug["id"], []):
        name = data.ingredient_names.get(row["ingredient_unii"])
        if not name:
            name = row["ingredient_unii"]

        result.append({"name": name, "strength": strength_text(data, row)})

    return result
