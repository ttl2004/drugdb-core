"""
Cột 20 — Khuyến cáo. Tiếng Anh.
Gộp theo thứ tự: Boxed Warning (34066-1), Warnings and Precautions (43685-7),
Warnings (34071-1), Precautions (42232-9).
"""

from etl2_csdl_qg.common.label_text import (choose_passages, is_kit, join_passages,
                                            outermost_sections, sections_by_code, sections_of,
                                            texts_of)

HEADER = "Khuyến cáo"

WARNING_CODES = ["34066-1", "43685-7", "34071-1", "42232-9"]


# Văn bản các mục cảnh báo của tài liệu, theo thứ tự WARNING_CODES.
# Chỉ lấy mục ngoài cùng: mục nằm trong một mục cảnh báo khác thì bỏ, tránh lặp văn bản.
# Tính một lần cho mỗi tài liệu rồi lưu vào data.cache.
def warning_texts(data, drug):
    key = (drug["document_id"], "khuyen_cao")

    if key not in data.cache:
        nodes = []
        for code in WARNING_CODES:
            nodes.extend(sections_by_code(sections_of(data, drug), code))

        data.cache[key] = texts_of(outermost_sections(nodes))

    return data.cache[key]


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []

    for drug in data.drugs:
        passages = choose_passages([warning_texts(data, drug)], drug, is_kit(data, drug))
        values.append(join_passages(passages))

    return values
