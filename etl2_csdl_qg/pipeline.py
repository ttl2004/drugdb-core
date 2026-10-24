import csv
import json
import os
import time

from etl2_csdl_qg.columns import (col01_nhom_thuoc, col02_ma_dinh_danh, col03_ten_thuoc,
                                  col04_loai_kiem_soat, col05_ke_don, col06_so_dang_ky,
                                  col07_ngay_cap, col08_ngay_het_hieu_luc, col09_ham_luong,
                                  col10_nha_san_xuat, col11_nuoc_san_xuat,
                                  col12_quy_cach_dong_goi, col13_duong_dung, col14_thanh_phan,
                                  col15_chi_dinh, col16_chong_chi_dinh, col17_bao_quan,
                                  col18_tac_dung, col19_tac_dung_phu, col20_khuyen_cao,
                                  col21_lieu_luong)
from etl2_csdl_qg.common.dictionary import Dictionary
from etl2_csdl_qg.common.input_data import load_input
from etl2_csdl_qg.constants import OUTPUT_FILE, TERMS_FILE
from etl2_csdl_qg.translate.deepseek import ApiKeyError
from etl2_csdl_qg.translate.dictionary_terms import count_empty_terms, read_terms, translate_missing

# 21 cột theo đúng thứ tự của file mẫu. Mỗi module có HEADER và build(data).
COLUMNS = [
    col01_nhom_thuoc,
    col02_ma_dinh_danh,
    col03_ten_thuoc,
    col04_loai_kiem_soat,
    col05_ke_don,
    col06_so_dang_ky,
    col07_ngay_cap,
    col08_ngay_het_hieu_luc,
    col09_ham_luong,
    col10_nha_san_xuat,
    col11_nuoc_san_xuat,
    col12_quy_cach_dong_goi,
    col13_duong_dung,
    col14_thanh_phan,
    col15_chi_dinh,
    col16_chong_chi_dinh,
    col17_bao_quan,
    col18_tac_dung,
    col19_tac_dung_phu,
    col20_khuyen_cao,
    col21_lieu_luong,
]

ALL_STEPS = ["build", "translate"]


# Cấu hình của một lần chạy ETL 2.
class Settings:
    # Lưu cấu hình; steps không truyền thì chạy đủ cả 2 bước.
    def __init__(self, input_dir, output_dir, dictionary_dir, api_url=None, model=None,
                 api_key=None, steps=None):
        self.input_dir = input_dir                # thư mục CSV của ETL 1
        self.output_dir = output_dir
        self.dictionary_dir = dictionary_dir      # thư mục 4 file từ điển
        self.api_url = api_url                    # DeepSeek, chỉ cần cho bước translate
        self.model = model
        self.api_key = api_key

        self.steps = steps
        if self.steps is None:
            self.steps = list(ALL_STEPS)


# Dòng tiêu đề 21 cột, lấy từ HEADER của từng module cột.
def header():
    names = []
    for column in COLUMNS:
        names.append(column.HEADER)
    return names


# Khoá sắp xếp dòng đầu ra: tên thuốc (cột 3, không phân biệt hoa thường), rồi mã định danh (cột 2).
def sort_key(row):
    return (row[2].lower(), row[1])


# Tạo các dòng đầu ra: mỗi module cột cho danh sách giá trị của cả cột,
# rồi ghép theo hàng (mỗi thuốc một dòng) và sắp theo sort_key.
def build_rows(data):
    columns = []
    for column in COLUMNS:
        columns.append(column.build(data))

    rows = []
    for i in range(len(data.drugs)):
        row = []
        for values in columns:
            row.append(values[i])
        rows.append(row)

    return sorted(rows, key=sort_key)


# Ghi file kết quả đúng định dạng file mẫu: UTF-8 không BOM, CRLF giữa các dòng.
def write_output(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header())
        writer.writerows(rows)


# Đếm số ô rỗng ở từng cột bắt buộc (tiêu đề có "(*)"): {số thứ tự cột: số ô rỗng}.
def empty_required_counts(rows):
    names = header()
    counts = {}

    for i in range(len(names)):
        if "(*)" not in names[i]:
            continue

        empty = 0
        for row in rows:
            if row[i] == "":
                empty += 1
        counts[i + 1] = empty

    return counts


# Tạo 21 cột, ghi ds-thuoc-dailymed.csv và dictionary_terms.csv, in tóm tắt.
# Trả về số liệu: số dòng, ô rỗng ở cột bắt buộc, số từ đã gặp / chưa dịch.
def build_and_write(data, settings, log):
    rows = build_rows(data)

    output_path = os.path.join(settings.output_dir, OUTPUT_FILE)
    terms_path = os.path.join(settings.output_dir, TERMS_FILE)
    write_output(output_path, rows)
    data.dictionary.write_terms(terms_path)

    empty = empty_required_counts(rows)
    terms = len(data.dictionary.seen)
    untranslated = data.dictionary.count_untranslated()

    # tóm tắt
    log("  đã ghi %d dòng -> %s" % (len(rows), output_path))
    log("  ô rỗng ở cột bắt buộc:")
    for number in empty:
        log("    cột %02d: %d" % (number, empty[number]))
    log("  từ điển: %d từ đã gặp, %d từ chưa dịch -> %s" % (terms, untranslated, terms_path))

    return {"rows": len(rows), "empty_required": empty, "terms": terms, "untranslated": untranslated}


# Bước translate: dịch các từ trống trong dictionary_terms.csv rồi, nếu từ điển có thêm
# bản dịch, đọc lại từ điển và build lại file kết quả. Trả về số liệu kèm khoá "ok".
# data là dữ liệu đã đọc ở bước build (None nếu chỉ chạy riêng bước này).
def run_translate(settings, data, log):
    terms_path = os.path.join(settings.output_dir, TERMS_FILE)

    # cần dictionary_terms.csv do bước build tạo ra
    if not os.path.exists(terms_path):
        log("  ! chưa có %s, hãy chạy bước build trước" % terms_path)
        return {"ok": False, "error": "missing dictionary_terms.csv"}

    # chỉ cần khoá API khi còn từ trống (bản dịch gõ tay thì chép thẳng, không gọi API)
    empty = count_empty_terms(read_terms(terms_path))
    log("  %d từ còn trống" % empty)
    if empty > 0 and not settings.api_key:
        log("  ! thiếu DEEPSEEK_API_KEY trong .env, không dịch được")
        return {"ok": False, "error": "missing DEEPSEEK_API_KEY"}

    try:
        results = translate_missing(settings, terms_path, log)
    except ApiKeyError as error:
        log("  ! %s; đã dừng" % error)
        return {"ok": False, "error": str(error)}

    # có thêm bản dịch thì build lại để file kết quả dùng từ điển mới
    changed = 0
    for name in results:
        changed += results[name]["copied"] + results[name]["translated"]

    if changed > 0:
        if data is None:
            log("\n[translate] Đọc lại CSV của ETL 1 để build lại")
            data = load_input(settings.input_dir, Dictionary(settings.dictionary_dir))
        else:
            data.dictionary.reload()

        log("\n[translate] Build lại với từ điển mới")
        rebuild = build_and_write(data, settings, log)
        return {"ok": True, "dictionaries": results, "rebuild": rebuild}

    return {"ok": True, "dictionaries": results}


# Chạy các bước của ETL 2 theo settings.steps và ghi _summary.json vào thư mục đầu ra.
# Trả về dict tổng kết; khoá "ok" = False nếu bước translate không chạy được
# (thiếu khoá API, khoá sai, chưa có dictionary_terms.csv).
def run(settings, log=print):
    os.makedirs(settings.output_dir, exist_ok=True)
    started = time.time()

    summary = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "input": settings.input_dir,
        "output": settings.output_dir,
        "steps": settings.steps,
    }
    ok = True
    data = None

    # bước 1: đọc dữ liệu, tạo 21 cột
    if "build" in settings.steps:
        log("\n[build] Đọc CSV của ETL 1")
        data = load_input(settings.input_dir, Dictionary(settings.dictionary_dir))
        log("  %d thuốc được xuất" % len(data.drugs))

        log("\n[build] Tạo 21 cột")
        summary["build"] = build_and_write(data, settings, log)

    # bước 2: dịch từ còn thiếu trong từ điển
    if "translate" in settings.steps:
        log("\n[translate] Dịch từ còn thiếu trong từ điển (DeepSeek)")
        summary["translate"] = run_translate(settings, data, log)
        if not summary["translate"]["ok"]:
            ok = False

    summary["elapsed_seconds"] = round(time.time() - started, 1)
    summary["ok"] = ok

    with open(os.path.join(settings.output_dir, "_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return summary
