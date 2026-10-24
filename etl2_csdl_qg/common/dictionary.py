import csv
import os

from etl2_csdl_qg.constants import DICTIONARY_NAMES


# Đọc một file từ điển thành dict {tiếng Anh: tiếng Việt}.
# Dòng có tiếng Việt rỗng coi như chưa dịch. Một từ có nhiều dòng thì lấy dòng
# đầu tiên có bản dịch.
def read_dictionary_file(path):
    words = {}

    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            english = row["tieng_anh"].strip()
            vietnamese = row["tieng_viet"].strip()

            if vietnamese != "" and english not in words:
                words[english] = vietnamese

    return words


# Bộ 4 từ điển, kèm danh sách từ đã tra trong lần tạo dữ liệu hiện tại.
class Dictionary:
    # Đọc 4 file từ điển trong thư mục folder.
    def __init__(self, folder):
        self.folder = folder

        # tên từ điển -> {tiếng Anh: tiếng Việt}
        self.words = {}

        # (tên từ điển, tiếng Anh) -> tập drug_id đã dùng từ đó
        self.seen = {}

        self.reload()

    # Đọc lại các file từ điển (sau khi có bản dịch mới) và xoá danh sách từ đã gặp.
    def reload(self):
        for name in DICTIONARY_NAMES:
            self.words[name] = read_dictionary_file(os.path.join(self.folder, name + ".csv"))

        self.seen = {}

    # Tra một từ trong từ điển name; trả về bản dịch, hoặc None nếu chưa có.
    # Đồng thời ghi nhớ từ này (và thuốc dùng nó) để xuất ra dictionary_terms.csv.
    def lookup(self, name, english, drug_id):
        key = (name, english)
        if key not in self.seen:
            self.seen[key] = set()
        self.seen[key].add(drug_id)

        return self.words[name].get(english)

    # Đếm số từ đã gặp mà chưa có bản dịch.
    def count_untranslated(self):
        count = 0
        for name, english in self.seen:
            if english not in self.words[name]:
                count += 1
        return count

    # Ghi dictionary_terms.csv: mọi từ đã gặp, bản dịch hiện có (rỗng nếu chưa dịch)
    # và số thuốc dùng từ đó. Ghi ra file tạm rồi thay file cũ, để không hỏng file nếu bị dừng.
    def write_terms(self, path):
        temp_path = path + ".tmp"

        with open(temp_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["tu_dien", "tieng_anh", "tieng_viet", "so_dong"])

            for key in sorted(self.seen):
                name, english = key
                vietnamese = self.words[name].get(english, "")
                writer.writerow([name, english, vietnamese, len(self.seen[key])])

        os.replace(temp_path, path)
