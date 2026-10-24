from etl1_spl.common.csv_table import TableModule
from etl1_spl.common.text import inner_xml, to_plain
from etl1_spl.common.xml_utils import NS, attr, display, txt


class LabelSection(TableModule):
    FILE = "label_section.csv"
    HEADER = ["id", "document_id", "parent_id", "anchor", "section_uuid",
              "loinc_code", "loinc_display", "title", "text_xml", "text_plain",
              "seq", "depth", "child_count"]

    # Khởi tạo bảng và bộ đếm id.
    def __init__(self, out_dir, settings):
        # phần chung của lớp cha: mở file CSV, ghi dòng tiêu đề
        super().__init__(out_dir, settings)

        # id tăng dần qua mọi tài liệu
        self.next_id = 1

    # Ghi toàn bộ cây mục nhãn của tài liệu.
    # Tài liệu không có section sản phẩm thì bỏ qua (giữ đúng như bản gốc).
    def process(self, doc):
        if doc.product_section is None:
            return

        self.walk(doc.body, doc.id, None, 1)

    # Duyệt đệ quy cây mục nhãn: container -> component -> section -> component ...
    # seq = thứ tự trong cùng mục cha, depth = độ sâu (1 = mục gốc).
    def walk(self, container, doc_id, parent_id, depth):
        seq = 0

        for component in container.findall(NS + "component"):
            section = component.find(NS + "section")
            if section is None:
                continue
            seq += 1

            code = section.find(NS + "code")
            text_el = section.find(NS + "text")

            # các mục con trực tiếp, để đếm child_count
            children = []
            for child_component in section.findall(NS + "component"):
                child = child_component.find(NS + "section")
                if child is not None:
                    children.append(child)

            # lấy id ngay tại đây, trước khi đi xuống mục con (mục con sẽ tăng bộ đếm)
            section_id = self.next_id
            self.next_id += 1

            # cột văn bản có thể tắt trong .env để file nhẹ hơn
            text_xml = None
            if self.settings.include_text_xml:
                text_xml = inner_xml(text_el)

            text_plain = None
            if self.settings.include_text_plain:
                text_plain = to_plain(text_el)

            self.write([
                section_id,
                doc_id,
                parent_id,
                attr(section, "ID"),
                attr(section.find(NS + "id"), "root"),
                attr(code, "code"),
                display(code),
                txt(section.find(NS + "title")),
                text_xml,
                text_plain,
                seq,
                depth,
                len(children),
            ])

            # đi xuống các mục con
            if children:
                self.walk(section, doc_id, section_id, depth + 1)
