HEADER = "Loại kiểm soát đặc biệt (*)"


# Giá trị cột cho mọi thuốc: tạm thời đều rỗng.
def build(data):
    values = []
    for drug in data.drugs:
        values.append("")
    return values
