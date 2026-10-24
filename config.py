import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")


# Đọc file .env thành một dict {tên: giá trị}.
# Thiếu file .env thì dừng chương trình và báo cần tạo từ .env.example.
def read_env(path):
    if not os.path.exists(path):
        raise SystemExit("ERROR: missing %s (copy .env.example to .env and fill it in)" % path)

    values = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()

            # bỏ dòng trống, dòng chú thích, dòng không có dấu =
            if line == "" or line.startswith("#") or "=" not in line:
                continue

            name, value = line.split("=", 1)
            values[name.strip()] = value.strip().strip('"')

    return values


ENV = read_env(ENV_FILE)


# Lấy giá trị một biến trong .env.
# Biến rỗng hoặc không có: dùng default; không có default thì dừng và báo lỗi.
def get(name, default=None):
    value = ENV.get(name, "")

    if value != "":
        return value

    if default is None:
        raise SystemExit("ERROR: %s is not set in %s" % (name, ENV_FILE))
    return default


# Lấy một đường dẫn trong .env và đổi thành đường dẫn tuyệt đối.
# Đường dẫn tương đối được tính từ thư mục Test-New-ETL.
def get_path(name, default=None):
    path = get(name, default)

    if not os.path.isabs(path):
        path = os.path.join(BASE_DIR, path)

    return os.path.normpath(path)


# Lấy một biến bật/tắt trong .env: 1, true, yes, on là bật; còn lại là tắt.
def get_bool(name, default=None):
    value = get(name, default).lower()
    return value in ("1", "true", "yes", "on")
