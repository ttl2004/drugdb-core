from etl2_csdl_qg.common.strength import active_ingredients

HEADER = "Hàm lượng"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs. Hoạt chất không có hàm lượng thì bỏ qua.
def build(data):
    values = []

    for drug in data.drugs:
        strengths = []
        for ingredient in active_ingredients(data, drug):
            if ingredient["strength"]:
                strengths.append(ingredient["strength"])

        values.append("; ".join(strengths))

    return values
