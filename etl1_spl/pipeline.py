import json
import os
import time
import xml.etree.ElementTree as ET

from etl1_spl.common import sources
from etl1_spl.common.document import parse_document
from etl1_spl.post import section_to_json, verify_csv
from etl1_spl.tables.drug_ingredient import DrugIngredient
from etl1_spl.tables.drug_knowledge import DrugKnowledge
from etl1_spl.tables.drug_package import DrugPackage
from etl1_spl.tables.drug_part import DrugPart
from etl1_spl.tables.ingredient import Ingredient
from etl1_spl.tables.label_document import LabelDocument
from etl1_spl.tables.label_section import LabelSection
from etl1_spl.tables.organization import Organization
from etl1_spl.tables.spl_document_index import process_dsv

# Các bảng lấy dữ liệu từ XML. Thêm bảng mới: tạo module trong tables/ rồi thêm vào đây.
TABLES = [
    LabelDocument,
    DrugKnowledge,
    DrugIngredient,
    LabelSection,
    DrugPackage,
    DrugPart,
    Organization,
    Ingredient,
]

ALL_STEPS = ["extract", "json", "verify"]


# Cấu hình của một lần chạy ETL 1.
class Settings:
    # Lưu cấu hình; steps không truyền thì chạy đủ cả 3 bước.
    def __init__(self, data_dir, output_dir, limit=None, include_text_xml=True,
                 include_text_plain=True, json_pretty=False, steps=None):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.limit = limit                        # chỉ lấy N thư mục con mỗi nhóm (chạy thử)
        self.include_text_xml = include_text_xml
        self.include_text_plain = include_text_plain
        self.json_pretty = json_pretty

        self.steps = steps
        if self.steps is None:
            self.steps = list(ALL_STEPS)


# Đọc lần lượt mọi file XML; mỗi file đọc một lần thành SplDocument rồi đưa cho
# từng bảng trong TABLES ghi dòng. File XML lỗi cú pháp thì ghi log và bỏ qua.
# Trả về {tên file CSV: {"rows": số dòng, "bytes": dung lượng}}.
def extract_xml(settings, log):
    files = sources.list_xml_files(settings.data_dir, settings.limit, log)
    total = len(files)
    log("  Tìm thấy %d tệp XML" % total)

    # mỗi lần chạy tạo bảng mới: mở file CSV, bộ đếm id bắt đầu lại từ đầu
    tables = []
    for table_class in TABLES:
        tables.append(table_class(settings.output_dir, settings))

    started = time.time()
    try:
        for i, (category, _sub, path) in enumerate(files, 1):
            # đọc file XML một lần
            try:
                doc = parse_document(category, path, settings.data_dir, log)
            except ET.ParseError as error:
                log("  ! lỗi parse %s: %s" % (path, error))
                continue

            # từng bảng ghi các dòng của tài liệu này
            for table in tables:
                table.process(doc)

            # báo tiến độ mỗi 250 file
            if i % 250 == 0 or i == total:
                elapsed = time.time() - started
                remaining = elapsed / i * (total - i)
                log("  [%5d/%d] %5.1f%%  %6.0fs  còn ~%.0fs"
                    % (i, total, 100.0 * i / total, elapsed, remaining))

        # bảng gom dữ liệu (organization, ingredient) ghi phần đã gom
        for table in tables:
            table.finish()

    finally:
        # luôn đóng file CSV, kể cả khi có lỗi giữa chừng
        results = {}
        for table in tables:
            rows, size = table.close()
            results[table.FILE] = {"rows": rows, "bytes": size}

    return results


# Chạy các bước của ETL 1 theo settings.steps và ghi _summary.json vào thư mục đầu ra.
# Trả về dict tổng kết; khoá "ok" = False nếu bước json hoặc verify phát hiện lỗi.
def run(settings, log=print):
    os.makedirs(settings.output_dir, exist_ok=True)
    started = time.time()

    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source": settings.data_dir,
        "output": settings.output_dir,
        "limit": settings.limit,
        "steps": settings.steps,
    }
    ok = True

    # bước 1: XML và DSV -> CSV
    if "extract" in settings.steps:
        log("\n[extract] Năm thư mục XML")
        summary["tables"] = extract_xml(settings, log)

        log("\n[extract] Thư mục DSV")
        summary["dsv"] = process_dsv(settings.data_dir, settings.output_dir, log)

    # bước 2: cây mục nhãn -> JSONL
    if "json" in settings.steps:
        log("\n[json] label_section.csv -> JSONL dạng cây")
        summary["json"] = section_to_json.run(settings.output_dir, settings.include_text_xml,
                                              settings.include_text_plain, settings.json_pretty, log)
        if not summary["json"]["ok"]:
            ok = False

    # bước 3: kiểm tra toàn vẹn (chạy toàn bộ thì so thêm số dòng thiết kế)
    if "verify" in settings.steps:
        log("\n[verify] Kiểm tra toàn vẹn")
        expect_full = settings.limit is None
        summary["verify"] = verify_csv.run(settings.output_dir, expect_full, log)
        if not summary["verify"]["ok"]:
            ok = False

    summary["elapsed_seconds"] = round(time.time() - started, 1)
    summary["ok"] = ok

    with open(os.path.join(settings.output_dir, "_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary
