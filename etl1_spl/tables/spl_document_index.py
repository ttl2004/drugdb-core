import hashlib
import os

from etl1_spl.common import sources
from etl1_spl.common.csv_table import Table
from etl1_spl.common.xml_utils import iso_date

HEADER = ["effective_time", "document_id", "set_id", "spl_version",
          "upload_date", "zip_filename", "ndc_list", "title"]


# Tính mã md5 của file, để phát hiện hai file DSV trùng nội dung.
def file_md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


# Chuyển một file DSV (cột ngăn bằng |) thành CSV.
# Dòng không đủ 8 cột bị bỏ và đếm vào bad_rows.
# Trả về (số dòng, dung lượng byte, số dòng lỗi).
def convert_dsv(source_path, out_path):
    table = Table(out_path, HEADER)
    bad_rows = 0

    with open(source_path, "r", encoding="utf-8", errors="replace") as f:
        # bỏ dòng tiêu đề của file DSV
        f.readline()

        for line in f:
            line = line.rstrip("\r\n")
            if not line:
                continue

            cols = line.split("|")
            if len(cols) != 8:
                bad_rows += 1
                continue

            # cột tiêu đề rỗng thì ghi None
            title = cols[7]
            if title == "":
                title = None

            table.writerow([
                iso_date(cols[0]),
                cols[1].lower(),
                cols[2].lower(),
                cols[3],
                cols[4],
                cols[5],
                cols[6],
                title,
            ])

    rows, size = table.close()
    return rows, size, bad_rows


# Chuyển các file DSV trong dash4dm_work thành CSV.
# File có chữ "delta" trong tên -> spl_document_delta.csv, còn lại -> spl_document_index.csv.
# Nhiều file cùng ra một CSV (vd hai bản full trùng nhau) thì chỉ ghi file đầu tiên.
# Trả về {tên CSV: thống kê, "_dsv_md5": {tên file: md5}}.
def process_dsv(root_dir, out_dir, log):
    found = sources.list_dsv_files(root_dir, log)
    if found is None:
        return {}
    log("  Tìm thấy %d tệp DSV" % len(found))

    results = {}
    fingerprints = {}

    for path in found:
        stem = os.path.splitext(os.path.basename(path))[0]
        fingerprints[stem] = file_md5(path)

        # chọn file CSV đích theo tên file DSV
        out_name = "spl_document_index.csv"
        if "delta" in stem:
            out_name = "spl_document_delta.csv"

        if out_name in results:
            log("  %s -> bỏ qua (đã ghi %s)" % (stem, out_name))
            continue

        rows, size, bad_rows = convert_dsv(path, os.path.join(out_dir, out_name))
        results[out_name] = {"rows": rows, "bytes": size, "source": stem, "bad_rows": bad_rows}
        log("  %s -> %s (%d dòng)" % (stem, out_name, rows))

    # báo nếu có hai file DSV trùng nội dung
    if len(set(fingerprints.values())) < len(fingerprints):
        log("  Lưu ý: có tệp DSV trùng nội dung (md5 giống nhau)")

    results["_dsv_md5"] = fingerprints
    return results
