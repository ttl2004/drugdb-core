from etl1_spl.common.csv_table import TableModule
from etl1_spl.common.document import is_active


class Ingredient(TableModule):
    FILE = "ingredient.csv"
    HEADER = ["unii", "name", "parent_unii", "is_active"]

    # Khởi tạo bảng và chỗ gom chất.
    def __init__(self, out_dir, settings):
        # phần chung của lớp cha: mở file CSV, ghi dòng tiêu đề
        super().__init__(out_dir, settings)

        # unii -> [unii, tên, parent_unii, is_active]
        self.items = {}

        # unii -> unii của chất gốc (activeMoiety)
        self.parents = {}

    # Gom các chất của tài liệu.
    # Một chất gặp lại thì giữ tên lần đầu; chỉ cần một lần là hoạt chất thì is_active = 1.
    def process(self, doc):
        for product in doc.products:
            for ingredient in product.ingredients:
                unii = ingredient.unii

                active = 0
                if is_active(ingredient.class_code):
                    active = 1

                # ghi nhớ chất gốc, gắn vào ở finish()
                if ingredient.parent_unii:
                    self.parents[unii] = ingredient.parent_unii

                # chất mới: thêm vào; chất đã có: chỉ cập nhật is_active
                if unii not in self.items:
                    name = ingredient.name
                    if not name:
                        name = unii
                    self.items[unii] = [unii, name, None, active]
                elif active == 1:
                    self.items[unii][3] = 1

    # Gắn chất gốc (parent_unii) rồi ghi các chất, sắp theo UNII.
    # Phải đợi cuối cùng vì chất gốc có thể xuất hiện ở tài liệu sau; chất gốc
    # không nằm trong danh sách thì bỏ trống.
    def finish(self):
        for unii in self.parents:
            parent = self.parents[unii]
            if unii in self.items and parent in self.items:
                self.items[unii][2] = parent

        for unii in sorted(self.items):
            self.write(self.items[unii])
