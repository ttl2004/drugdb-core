import uuid
import xml.etree.ElementTree as ET

# Mọi thẻ trong file SPL đều mang namespace của chuẩn HL7 v3 ở đầu tên
NS = "{urn:hl7-org:v3}"
NS_URI = "urn:hl7-org:v3"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"

# Khi ghi XML ra chuỗi (cột text_xml), giữ tiền tố namespace giống file gốc
ET.register_namespace("", NS_URI)
ET.register_namespace("xsi", NS_XSI)

# Gốc để sinh UUID cố định cho thuốc
NS_UUID = uuid.UUID("6f1a5c2e-9d3b-4f7a-8e21-0c4b7a9d5e13")


# Lấy tên thẻ, bỏ phần namespace phía trước.
# Ví dụ: "{urn:hl7-org:v3}section" -> "section".
def tag(el):
    # chú thích XML (<!-- -->) không có tên thẻ
    if not isinstance(el.tag, str):
        return ""

    return el.tag.replace(NS, "")


# Lấy chữ bên trong một thẻ, gộp khoảng trắng / xuống dòng thừa thành một dấu cách.
# Thẻ không tồn tại hoặc không có chữ thì trả về None.
def txt(el):
    if el is None or el.text is None:
        return None

    text = " ".join(el.text.split())

    if text == "":
        return None
    return text


# Lấy một thuộc tính của thẻ, đã bỏ khoảng trắng hai đầu.
# Thẻ không tồn tại, không có thuộc tính hoặc thuộc tính rỗng thì trả về None.
def attr(el, name):
    if el is None:
        return None

    value = el.get(name)
    if value is None:
        return None

    value = value.strip()
    if value == "":
        return None
    return value


# Lấy displayName (tên hiển thị của một mã, vd dạng bào chế "TABLET") và viết hoa.
# Không có thì trả về None.
def display(el):
    name = attr(el, "displayName")

    if name is None:
        return None
    return name.upper()


# Sinh id (UUID v5) cho một thuốc từ cặp (document_id, NDC).
# Cùng dữ liệu thì chạy lại bao nhiêu lần cũng ra cùng id, nên các bảng liên kết không bị lệch.
def stable_id(document_id, ndc):
    key = str(document_id) + "|" + str(ndc)
    return str(uuid.uuid5(NS_UUID, key))


# Đổi ngày dạng 20260820 thành 2026-08-20.
# Giá trị không phải ngày hợp lệ thì giữ nguyên.
def iso_date(value):
    if not value or len(value) < 8 or not value[:8].isdigit():
        return value

    return value[0:4] + "-" + value[4:6] + "-" + value[6:8]


# Đổi chuỗi số thành số thực (vd "10" -> 10.0).
# Không phải số thì giữ nguyên chuỗi; None giữ None.
def num(value):
    if value is None:
        return None

    try:
        return float(value)
    except ValueError:
        return value


# Lấy tử số và mẫu số của một thẻ <quantity> (vd hàm lượng 500 mg / 5 mL).
# Trả về (numerator, denominator); thiếu thẻ thì là None.
def quantity(el):
    if el is None:
        return None, None

    numerator = el.find(NS + "numerator")
    denominator = el.find(NS + "denominator")
    return numerator, denominator
