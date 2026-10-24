from etl1_spl.common.csv_table import TableModule
from etl1_spl.common.xml_utils import attr, num


class DrugPart(TableModule):
    FILE = "drug_part.csv"
    HEADER = ["id", "parent_drug_id", "part_drug_id", "seq",
              "qty_value", "qty_unit", "basis_value", "basis_unit"]

    # Khởi tạo bảng và bộ đếm id.
    def __init__(self, out_dir, settings):
        # phần chung của lớp cha: mở file CSV, ghi dòng tiêu đề
        super().__init__(out_dir, settings)

        # id tăng dần qua mọi tài liệu
        self.last_id = 0

    # Ghi liên kết giữa bộ combo và từng sản phẩm thành phần có NDC, kèm số lượng.
    def process(self, doc):
        for product in doc.products:
            for part in product.parts:
                # thành phần không có NDC thì không phải thuốc riêng, không liên kết
                if not part.ndc:
                    continue

                self.last_id += 1
                self.write([
                    self.last_id,
                    product.drug_id,
                    part.drug_id,
                    part.part_index,
                    num(attr(part.numerator, "value")),
                    attr(part.numerator, "unit"),
                    num(attr(part.denominator, "value")),
                    attr(part.denominator, "unit"),
                ])
