from etl1_spl.common.csv_table import TableModule
from etl1_spl.common.xml_utils import NS, attr, display, num, quantity


class DrugPackage(TableModule):
    FILE = "drug_package.csv"
    HEADER = ["id", "drug_id", "parent_id", "ndc", "form_code", "form_name",
              "qty_value", "qty_unit", "basis_value", "basis_unit", "level"]

    # Khởi tạo bảng và bộ đếm id.
    def __init__(self, out_dir, settings):
        # phần chung của lớp cha: mở file CSV, ghi dòng tiêu đề
        super().__init__(out_dir, settings)

        # id tăng dần qua mọi tài liệu
        self.next_id = 1

    # Ghi cây bao bì của từng sản phẩm, rồi của các sản phẩm thành phần combo.
    # Thành phần combo không có NDC (35 trường hợp) thì cây bao bì gắn vào thuốc cha.
    def process(self, doc):
        for product in doc.products:
            self.walk(product.element, product.drug_id, None, 1)

            for part in product.parts:
                drug_id = part.drug_id
                if drug_id is None:
                    drug_id = product.drug_id
                self.walk(part.element, drug_id, None, 1)

    # Duyệt đệ quy cây bao bì: asContent -> containerPackagedProduct -> asContent ...
    # Mỗi asContent là một tầng; level = độ sâu (1 = tầng ngoài cùng).
    def walk(self, container, drug_id, parent_id, level):
        for content in container.findall(NS + "asContent"):
            package = content.find(NS + "containerPackagedProduct")
            numerator, denominator = quantity(content.find(NS + "quantity"))

            # mã NDC và dạng bao bì của tầng này
            code = None
            form = None
            if package is not None:
                code = package.find(NS + "code")
                form = package.find(NS + "formCode")

            # lấy id cho tầng này trước khi đi xuống tầng con
            package_id = self.next_id
            self.next_id += 1

            self.write([
                package_id,
                drug_id,
                parent_id,
                attr(code, "code"),
                attr(form, "code"),
                display(form),
                num(attr(numerator, "value")),
                attr(numerator, "unit"),
                num(attr(denominator, "value")),
                attr(denominator, "unit"),
                level,
            ])

            # đi xuống tầng bên trong
            if package is not None:
                self.walk(package, drug_id, package_id, level + 1)
