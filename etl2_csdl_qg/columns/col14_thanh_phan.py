from etl2_csdl_qg.common.formatting import capitalize_name
from etl2_csdl_qg.common.strength import active_ingredients

HEADER = "Thành phần"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []

    for drug in data.drugs:
        parts = []
        for ingredient in active_ingredients(data, drug):
            name = capitalize_name(ingredient["name"])

            if ingredient["strength"]:
                parts.append(name + " " + ingredient["strength"])
            else:
                parts.append(name)

        values.append("; \n".join(parts))

    return values
