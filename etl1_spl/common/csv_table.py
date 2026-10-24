import csv
import os


# Một file CSV đang mở để ghi (UTF-8 có BOM, xuống dòng LF).
class Table:
    # Mở file CSV và ghi ngay dòng tiêu đề.
    def __init__(self, path, header):
        self.path = path
        self.n = 0
        self.fh = open(path, "w", newline="", encoding="utf-8-sig")
        self.writer = csv.writer(self.fh, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        self.writer.writerow(header)

    # Ghi một dòng dữ liệu và đếm số dòng đã ghi.
    def writerow(self, row):
        self.writer.writerow(row)
        self.n += 1

    # Đóng file; trả về (số dòng, dung lượng byte) để báo cáo.
    def close(self):
        self.fh.close()
        size = os.path.getsize(self.path)
        return self.n, size


# Khuôn chung của một bảng đầu ra. Mỗi file trong tables/ là một lớp con, khai báo:
#
#     FILE          tên file CSV
#     HEADER        danh sách cột
#     process(doc)  đọc một tài liệu XML (SplDocument) thì ghi những dòng nào
#     finish()      chạy một lần cuối cùng, cho bảng cần gom dữ liệu rồi mới ghi
#
# Mỗi lần chạy ETL tạo một đối tượng mới, nên bộ đếm id và dữ liệu gom
# luôn bắt đầu lại từ đầu, không dính sang lần chạy sau.
class TableModule:
    FILE = None
    HEADER = None

    # Phần chung của mọi bảng: giữ cấu hình, mở file CSV và ghi dòng tiêu đề.
    def __init__(self, out_dir, settings):
        self.settings = settings
        self.table = Table(os.path.join(out_dir, self.FILE), self.HEADER)

    # Ghi một dòng vào file CSV của bảng.
    def write(self, row):
        self.table.writerow(row)

    # Lớp con bắt buộc tự viết hàm này.
    def process(self, doc):
        raise NotImplementedError

    # Mặc định không làm gì; bảng nào cần gom dữ liệu thì tự viết lại.
    def finish(self):
        pass

    # Đóng file CSV; trả về (số dòng, dung lượng byte).
    def close(self):
        return self.table.close()
