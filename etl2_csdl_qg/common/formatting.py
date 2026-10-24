"""
formatting.py — Định dạng giá trị theo kiểu file mẫu CSDL Dược (số, ngày, tên).
"""


# Định dạng số theo kiểu Việt Nam: bỏ phần thập phân thừa, dấu thập phân là dấu phẩy.
# Ví dụ: "10.0" -> "10", "4.2" -> "4,2". Không phải số thì giữ nguyên.
def format_number(value):
    if value == "":
        return ""

    try:
        number = float(value)
    except ValueError:
        return value

    # tối đa 6 chữ số thập phân, bỏ số 0 và dấu chấm thừa ở cuối
    text = ("%.6f" % number).rstrip("0").rstrip(".")
    return text.replace(".", ",")


# Đổi ngày "2026-08-20" thành "20/08/2026".
# Rỗng hoặc sai định dạng thì trả về chuỗi rỗng.
def format_date(iso_date):
    if not iso_date or len(iso_date) < 10:
        return ""

    return iso_date[8:10] + "/" + iso_date[5:7] + "/" + iso_date[0:4]


# Tên viết hoa toàn bộ thì chỉ giữ hoa chữ đầu: "ACETAMINOPHEN" -> "Acetaminophen".
# Tên đã có chữ thường thì giữ nguyên.
def capitalize_name(name):
    if name.isupper():
        return name[:1] + name[1:].lower()
    return name
