import argparse
import os
import sys

# python -I không tự thêm thư mục của script vào sys.path: thêm vào để import được etl1_spl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from etl1_spl import pipeline


# Đọc tham số dòng lệnh.
def parse_args():
    parser = argparse.ArgumentParser(description="ETL 1: trích xuất SPL ra CSV")
    parser.add_argument("--root", help="thư mục dữ liệu gốc (mặc định SPL_DATA_DIR)")
    parser.add_argument("--out", help="thư mục đầu ra (mặc định ETL1_OUTPUT_DIR)")
    parser.add_argument("--limit", type=int, help="chỉ xử lý N thư mục mỗi nhóm")
    parser.add_argument("--no-plain", action="store_true", help="bỏ cột text_plain")
    parser.add_argument("--no-xml", action="store_true", help="bỏ cột text_xml")
    parser.add_argument("--steps", default=",".join(pipeline.ALL_STEPS),
                        help="các bước, cách nhau bởi dấu phẩy: " + ", ".join(pipeline.ALL_STEPS))
    return parser, parser.parse_args()


# Tách chuỗi "extract,json" thành danh sách bước; bước không hợp lệ thì báo lỗi và dừng.
def read_steps(parser, text):
    steps = []

    for step in text.split(","):
        step = step.strip()
        if step == "":
            continue
        if step not in pipeline.ALL_STEPS:
            parser.error("bước không hợp lệ: %s" % step)
        steps.append(step)

    return steps


# Ghép cấu hình .env với tham số dòng lệnh (tham số dòng lệnh được ưu tiên).
def build_settings(parser, args):
    # thư mục dữ liệu gốc và thư mục đầu ra
    if args.root:
        data_dir = os.path.abspath(args.root)
    else:
        data_dir = config.get_path("SPL_DATA_DIR")

    if args.out:
        output_dir = os.path.abspath(args.out)
    else:
        output_dir = config.get_path("ETL1_OUTPUT_DIR")

    # cột văn bản: tắt nếu .env tắt hoặc có tham số --no-xml / --no-plain
    include_text_xml = config.get_bool("ETL1_INCLUDE_TEXT_XML", "1")
    if args.no_xml:
        include_text_xml = False

    include_text_plain = config.get_bool("ETL1_INCLUDE_TEXT_PLAIN", "1")
    if args.no_plain:
        include_text_plain = False

    return pipeline.Settings(
        data_dir=data_dir,
        output_dir=output_dir,
        limit=args.limit,
        include_text_xml=include_text_xml,
        include_text_plain=include_text_plain,
        json_pretty=config.get_bool("ETL1_JSON_PRETTY", "0"),
        steps=read_steps(parser, args.steps),
    )


# In một dòng log ra màn hình ngay lập tức.
def log(message):
    print(message, flush=True)


# In bảng số dòng và dung lượng của từng file CSV đã ghi.
def print_file_table(summary):
    files = {}
    for name in summary["tables"]:
        files[name] = summary["tables"][name]
    for name in summary["dsv"]:
        if name.endswith(".csv"):
            files[name] = summary["dsv"][name]

    log("\n" + "=" * 72)
    log("%-28s %10s %12s" % ("FILE", "DÒNG", "DUNG LƯỢNG"))
    log("-" * 72)

    total_rows = 0
    for name in sorted(files):
        rows = files[name]["rows"]
        size_mb = files[name]["bytes"] / 1048576
        total_rows += rows
        log("%-28s %10d %9.1f MB" % (name, rows, size_mb))

    log("-" * 72)
    log("%-28s %10d" % ("TỔNG", total_rows))


# Đọc cấu hình, chạy pipeline và in kết quả. Trả về 0 nếu thành công, 1 nếu có lỗi.
def main():
    # console Windows mặc định cp1252, sẽ lỗi khi in tiếng Việt
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser, args = parse_args()
    settings = build_settings(parser, args)

    log("=" * 72)
    log("ETL 1: SPL -> CSV")
    log("  nguồn : %s" % settings.data_dir)
    log("  đích  : %s" % settings.output_dir)
    log("  bước  : %s" % ", ".join(settings.steps))
    if settings.limit:
        log("  GIỚI HẠN: %d thư mục mỗi nhóm (chạy thử)" % settings.limit)
    log("=" * 72)

    summary = pipeline.run(settings, log)

    if "tables" in summary:
        print_file_table(summary)

    status = "CÓ LỖI"
    if summary["ok"]:
        status = "OK"
    log("\nHoàn tất sau %.0f giây (%s). Kèm báo cáo: _summary.json" % (summary["elapsed_seconds"], status))

    if summary["ok"]:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
