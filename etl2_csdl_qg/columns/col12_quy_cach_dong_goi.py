from etl2_csdl_qg.common.formatting import format_number
from etl2_csdl_qg.common.strength import unit_text

HEADER = "Quy cách đóng gói"


# Phần trước dấu phẩy của tên dạng: "BOTTLE, PLASTIC" -> "BOTTLE".
def first_word(form_name):
    return form_name.split(",")[0].strip()


# Tên bao bì tiếng Việt (vd CARTON -> hộp); chưa có trong từ điển thì giữ tiếng Anh viết thường.
def package_name(data, form_name, drug_id):
    word = first_word(form_name)
    if word == "":
        return ""

    vietnamese = data.dictionary.lookup("bao_bi", word, drug_id)
    if vietnamese is None:
        return word.lower()
    return vietnamese


# Đơn vị đếm theo dạng bào chế (vd TABLET -> viên); chưa có trong từ điển thì giữ tiếng Anh viết thường.
def count_unit(data, dosage_form, drug_id):
    word = first_word(dosage_form)
    if word == "":
        return ""

    vietnamese = data.dictionary.lookup("don_vi_dem", word, drug_id)
    if vietnamese is None:
        return word.lower()
    return vietnamese


# "3" + "vỉ" -> "3 vỉ"; tên rỗng thì chỉ có số.
def number_with_name(number, name):
    if name == "":
        return number
    return number + " " + name


# Số lượng ở tầng trong cùng: có đơn vị đo thì "100 mL", không có thì đếm theo
# dạng bào chế, vd "10 viên". Không ghi số thì coi là 1.
def innermost_quantity(data, value, unit, dosage_form, drug_id):
    number = format_number(value)
    if number == "":
        number = "1"

    if unit == "" or unit == "1":
        return number_with_name(number, count_unit(data, dosage_form, drug_id))

    return number + " " + unit_text(data, unit, drug_id)


# Đổi cây bao bì của một thuốc thành các câu mô tả, vd ["Hộp 3 vỉ x 10 viên", ...].
# Mỗi nút ghi số lượng của thứ nằm bên trong nó; parent_id trỏ vào lớp bên trong.
# Mỗi nút ngoài cùng cho một câu; câu trùng thì bỏ.
def package_descriptions(data, nodes, dosage_form):
    # tra nút theo id, và đánh dấu nút nào là lớp bên trong của nút khác
    by_id = {}
    inner_ids = set()
    for node in nodes:
        by_id[node["id"]] = node
        if node["parent_id"]:
            inner_ids.add(node["parent_id"])

    result = []

    for outer in nodes:
        # chỉ bắt đầu từ nút ngoài cùng
        if outer["id"] in inner_ids:
            continue

        # chuỗi bao bì từ ngoài cùng vào trong cùng
        chain = [outer]
        while chain[-1]["parent_id"] and chain[-1]["parent_id"] in by_id:
            chain.append(by_id[chain[-1]["parent_id"]])

        # mỗi tầng: số lượng + tên tầng bên trong, vd "3 vỉ"
        parts = []
        for i in range(len(chain) - 1):
            number = format_number(chain[i]["qty_value"])
            if number == "":
                number = "1"
            inner = chain[i + 1]
            parts.append(number_with_name(number, package_name(data, inner["form_name"], inner["drug_id"])))

        # tầng trong cùng: số lượng thuốc, vd "10 viên"
        innermost = chain[-1]
        parts.append(innermost_quantity(data, innermost["qty_value"], innermost["qty_unit"],
                                        dosage_form, innermost["drug_id"]))

        # tên bao bì ngoài cùng viết hoa chữ đầu, đặt trước: "Hộp 3 vỉ x 10 viên"
        description = " x ".join(parts)
        outer_name = package_name(data, chain[0]["form_name"], chain[0]["drug_id"])
        if outer_name != "":
            description = outer_name[:1].upper() + outer_name[1:] + " " + description

        if description not in result:
            result.append(description)

    return result


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []

    for drug in data.drugs:
        nodes = data.packages.get(drug["id"], [])
        descriptions = package_descriptions(data, nodes, drug["form_name"])
        values.append("; ".join(descriptions))

    return values
