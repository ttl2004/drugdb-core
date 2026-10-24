import time

from etl1_spl.common.csv_table import TableModule
from etl1_spl.common.xml_utils import NS, attr, display, iso_date, txt


class LabelDocument(TableModule):
    FILE = "label_document.csv"
    HEADER = ["id", "set_id", "version", "doc_code", "doc_code_display",
              "effective_time", "title", "labeler_id", "body_type",
              "has_related_doc", "source_category", "source_path", "imported_at"]

    # Ghi một dòng thông tin chung của tài liệu.
    def process(self, doc):
        root = doc.root

        # số phiên bản: chỉ nhận khi là số
        version = None
        if doc.version and doc.version.isdigit():
            version = int(doc.version)

        # tổ chức đứng tên nhãn
        labeler_id = None
        if doc.labeler:
            labeler_id = doc.labeler[0]

        # structured = có phần thân XML, nonxml = chỉ có file đính kèm
        body_type = "nonxml"
        if doc.body is not None:
            body_type = "structured"

        # tài liệu có tham chiếu tới tài liệu khác không
        has_related_doc = 0
        if root.find(NS + "relatedDocument") is not None:
            has_related_doc = 1

        self.write([
            doc.id,
            doc.set_id,
            version,
            attr(doc.code, "code"),
            display(doc.code),
            iso_date(attr(root.find(NS + "effectiveTime"), "value")),
            txt(root.find(NS + "title")),
            labeler_id,
            body_type,
            has_related_doc,
            doc.category,
            doc.source_path,
            time.strftime("%Y-%m-%d %H:%M:%S"),
        ])
