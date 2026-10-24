from etl1_spl.common.csv_table import TableModule
from etl1_spl.common.document import is_active
from etl1_spl.common.xml_utils import attr, display


class DrugKnowledge(TableModule):
    FILE = "drug_knowledge.csv"
    HEADER = ["id", "document_id", "ndc", "name", "generic_name",
              "form_code", "form_name", "route_code", "route_name",
              "manufacturer_id", "manufacturer_name", "approval_code",
              "item_seq", "has_active",
              "approval_id", "dea_schedule", "marketing_start", "marketing_end"]

    # Ghi mỗi sản phẩm một dòng, ngay sau đó là các sản phẩm thành phần combo mới của nó.
    # Sản phẩm thành phần thừa hưởng phê duyệt, DEA, ngày lưu hành của bộ cha.
    def process(self, doc):
        # nhà sản xuất dùng chung cho mọi sản phẩm trong tài liệu
        manufacturer_id = None
        manufacturer_name = None
        if doc.manufacturer:
            manufacturer_id = doc.manufacturer[0]
            manufacturer_name = doc.manufacturer[1]

        for product in doc.products:
            self.write([
                product.drug_id,
                doc.id,
                product.ndc,
                product.name,
                product.generic_name,
                attr(product.form, "code"),
                display(product.form),
                attr(product.route, "code"),
                display(product.route),
                manufacturer_id,
                manufacturer_name,
                attr(product.approval, "displayName"),
                product.item_seq,
                self.has_active(product),
                product.approval_id,
                product.dea_schedule,
                product.marketing_start,
                product.marketing_end,
            ])

            # sản phẩm thành phần combo có NDC chưa ghi trong tài liệu
            for part in product.parts:
                if not part.is_new:
                    continue

                self.write([
                    part.drug_id,
                    doc.id,
                    part.ndc,
                    part.name,
                    None,
                    attr(part.form, "code"),
                    display(part.form),
                    attr(part.route, "code"),
                    display(part.route),
                    manufacturer_id,
                    manufacturer_name,
                    None,
                    part.item_seq,
                    0,
                    product.approval_id,
                    product.dea_schedule,
                    product.marketing_start,
                    product.marketing_end,
                ])

    # Trả về 1 nếu sản phẩm có ít nhất một hoạt chất, ngược lại 0.
    def has_active(self, product):
        for ingredient in product.ingredients:
            if is_active(ingredient.class_code):
                return 1
        return 0
