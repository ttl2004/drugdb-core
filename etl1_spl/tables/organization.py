from etl1_spl.common.csv_table import TableModule


class Organization(TableModule):
    FILE = "organization.csv"
    HEADER = ["id", "name", "id_root"]

    # Khởi tạo bảng và chỗ gom tổ chức.
    def __init__(self, out_dir, settings):
        # phần chung của lớp cha: mở file CSV, ghi dòng tiêu đề
        super().__init__(out_dir, settings)

        # duns -> [duns, tên, id_root]
        self.items = {}

    # Gom các tổ chức của tài liệu; một DUNS gặp lại thì giữ tên của lần gặp đầu tiên.
    def process(self, doc):
        for org in doc.org_chain:
            duns, name, id_root, _depth = org

            if duns in self.items:
                continue

            # không có tên thì dùng tạm mã DUNS
            if not name:
                name = duns
            self.items[duns] = [duns, name, id_root]

    # Ghi các tổ chức đã gom, sắp theo mã DUNS.
    def finish(self):
        for duns in sorted(self.items):
            self.write(self.items[duns])
