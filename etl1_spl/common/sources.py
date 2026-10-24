import os

XML_CATEGORIES = ["animal", "homeopathic", "otc", "other", "prescription"]
DSV_CATEGORY = "dash4dm_work"


# Tìm mọi file .xml trong 5 thư mục nhóm thuốc, theo thứ tự tên thư mục / tên file.
# limit: chỉ lấy N thư mục con đầu tiên mỗi nhóm (để chạy thử); None là lấy hết.
# Trả về danh sách (nhóm, thư mục con, đường dẫn file).
def list_xml_files(root_dir, limit, log):
    files = []

    for category in XML_CATEGORIES:
        category_dir = os.path.join(root_dir, category)
        if not os.path.isdir(category_dir):
            log("  ! thiếu thư mục %s" % category)
            continue

        # các thư mục con của nhóm, sắp theo tên
        sub_dirs = []
        for name in os.listdir(category_dir):
            if os.path.isdir(os.path.join(category_dir, name)):
                sub_dirs.append(name)
        sub_dirs.sort()

        if limit:
            sub_dirs = sub_dirs[:limit]

        # các file .xml trong từng thư mục con, sắp theo tên
        for sub in sub_dirs:
            sub_dir = os.path.join(category_dir, sub)
            for name in sorted(os.listdir(sub_dir)):
                if name.lower().endswith(".xml"):
                    files.append((category, sub, os.path.join(sub_dir, name)))

    return files


# Tìm mọi file .dsv trong thư mục dash4dm_work (kể cả thư mục con).
# Thiếu thư mục thì trả về None.
def list_dsv_files(root_dir, log):
    base = os.path.join(root_dir, DSV_CATEGORY)
    if not os.path.isdir(base):
        log("  ! thiếu thư mục %s" % DSV_CATEGORY)
        return None

    found = []
    for dir_path, _sub_dirs, names in os.walk(base):
        for name in sorted(names):
            if name.lower().endswith(".dsv"):
                found.append(os.path.join(dir_path, name))

    return found
