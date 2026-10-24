from etl1_spl.common.csv_table import TableModule
from etl1_spl.common.xml_utils import attr, num


class DrugIngredient(TableModule):
    FILE = "drug_ingredient.csv"
    HEADER = ["id", "drug_id", "ingredient_unii", "class_code",
              "strength_value", "strength_unit", "basis_value", "basis_unit",
              "display_order"]

    # Khởi tạo bảng và bộ đếm id.
    def __init__(self, out_dir, settings):
        # phần chung của lớp cha: mở file CSV, ghi dòng tiêu đề
        super().__init__(out_dir, settings)

        # id tăng dần qua mọi tài liệu
        self.last_id = 0

    # Ghi các thành phần của từng sản phẩm.
    # Hàm lượng = tử số / mẫu số (vd 500 mg / 5 mL); display_order đánh 1..n trong mỗi thuốc.
    def process(self, doc):
        for product in doc.products:
            order = 0

            for ingredient in product.ingredients:
                self.last_id += 1
                order += 1

                self.write([
                    self.last_id,
                    product.drug_id,
                    ingredient.unii,
                    ingredient.class_code,
                    num(attr(ingredient.numerator, "value")),
                    attr(ingredient.numerator, "unit"),
                    num(attr(ingredient.denominator, "value")),
                    attr(ingredient.denominator, "unit"),
                    order,
                ])
