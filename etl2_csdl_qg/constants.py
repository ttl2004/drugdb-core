"""
constants.py — Hằng số dùng chung của ETL 2.
"""

# Loại tài liệu bị bỏ: CSDL Dược chỉ quản lý thuốc dùng cho người
EXCLUDED_DOC_TYPES = [
    "OTC ANIMAL DRUG LABEL",
    "PRESCRIPTION ANIMAL DRUG LABEL",
    "BULK INGREDIENT - ANIMAL DRUG",
    "VFD TYPE A MEDICATED ARTICLE ANIMAL DRUG LABEL",
    "DIETARY SUPPLEMENT",
    "MEDICAL FOOD",
]

# Loại tài liệu được coi là thuốc kê đơn
PRESCRIPTION_DOC_TYPES = [
    "HUMAN PRESCRIPTION DRUG LABEL",
    "VACCINE LABEL",
    "PLASMA DERIVATIVE",
]

# class_code của hoạt chất trong drug_ingredient
ACTIVE_CLASS_CODES = ["ACTIB", "ACTIM", "ACTIR"]

# Dữ liệu DailyMed chỉ có thuốc lưu hành tại Mỹ
COUNTRY = "US"

# route_name này nghĩa là không có đường dùng -> để trống, không cần dịch
ROUTE_NOT_APPLICABLE = "NOT APPLICABLE"

# Tên các từ điển Anh -> Việt (mỗi từ điển là một file <tên>.csv trong thư mục từ điển)
DICTIONARY_NAMES = ["duong_dung", "bao_bi", "don_vi_dem", "don_vi"]

# Tên file đầu ra
OUTPUT_FILE = "ds-thuoc-dailymed.csv"
TERMS_FILE = "dictionary_terms.csv"
