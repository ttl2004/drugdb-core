import argparse
import os
import sys

# python -I không tự thêm thư mục của script vào sys.path: thêm vào để import được etl2_csdl_qg
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from etl2_csdl_qg import pipeline


# Đọc tham số dòng lệnh.
def parse_args():
    parser = argparse.ArgumentParser(description="ETL 2: CSV của ETL 1 -> 21 cột CSDL Dược quốc gia")
    parser.add_argument("--input", help="thư mục CSV của ETL 1 (mặc định ETL2_INPUT_DIR)")
    parser.add_argument("--out", help="thư mục đầu ra (mặc định ETL2_OUTPUT_DIR)")
    parser.add_argument("--steps", default=",".join(pipeline.ALL_STEPS),
                        help="các bước, cách nhau bởi dấu phẩy: " + ", ".join(pipeline.ALL_STEPS))
    return parser, parser.parse_args()


# Tách chuỗi "build,translate" thành danh sách bước; bước không hợp lệ thì báo lỗi và dừng.
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
    if args.input:
        input_dir = os.path.abspath(args.input)
    else:
        input_dir = config.get_path("ETL2_INPUT_DIR")

    if args.out:
        output_dir = os.path.abspath(args.out)
    else:
        output_dir = config.get_path("ETL2_OUTPUT_DIR")

    # khoá API được phép để trống: chỉ bước translate cần
    return pipeline.Settings(
        input_dir=input_dir,
        output_dir=output_dir,
        dictionary_dir=config.get_path("ETL2_DICTIONARY_DIR"),
        api_url=config.get("DEEPSEEK_API_URL", ""),
        model=config.get("DEEPSEEK_MODEL", ""),
        api_key=config.get("DEEPSEEK_API_KEY", ""),
        steps=read_steps(parser, args.steps),
    )


# In một dòng log ra màn hình ngay lập tức.
def log(message):
    print(message, flush=True)


# Đọc cấu hình, chạy pipeline và in kết quả. Trả về 0 nếu thành công, 1 nếu có lỗi.
def main():
    # console Windows mặc định cp1252, sẽ lỗi khi in tiếng Việt
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser, args = parse_args()
    settings = build_settings(parser, args)

    log("=" * 72)
    log("ETL 2: CSV ETL 1 -> 21 cột CSDL Dược quốc gia")
    log("  nguồn  : %s" % settings.input_dir)
    log("  đích   : %s" % settings.output_dir)
    log("  từ điển: %s" % settings.dictionary_dir)
    log("  bước   : %s" % ", ".join(settings.steps))
    log("=" * 72)

    summary = pipeline.run(settings, log)

    status = "CÓ LỖI"
    if summary["ok"]:
        status = "OK"
    log("\nHoàn tất sau %.0f giây (%s). Kèm báo cáo: _summary.json" % (summary["elapsed_seconds"], status))

    if summary["ok"]:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
