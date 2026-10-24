HEADER = "Số đăng ký lưu hành (*)"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []
    for drug in data.drugs:
        values.append(drug["approval_id"])
    return values
