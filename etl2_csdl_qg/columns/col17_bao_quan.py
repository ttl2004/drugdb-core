from etl2_csdl_qg.common.label_text import (children_of, choose_passages, first_section_by_title,
                                            is_kit, join_passages, sections_by_code, sections_of,
                                            texts_for_code, texts_of)

HEADER = "Cách bảo quản"


# Văn bản dự phòng: trong mỗi mục How Supplied, lấy mục con đầu tiên có tiêu đề chứa "stor"
# (Storage, Store ...). Tính một lần cho mỗi tài liệu rồi lưu vào data.cache.
def fallback_texts(data, drug):
    key = (drug["document_id"], "bao_quan_du_phong")

    if key not in data.cache:
        nodes = []
        for how_supplied in sections_by_code(sections_of(data, drug), "34069-5"):
            node = first_section_by_title(children_of(how_supplied), r"stor")
            if node is not None:
                nodes.append(node)

        data.cache[key] = texts_of(nodes)

    return data.cache[key]


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []

    for drug in data.drugs:
        groups = [texts_for_code(data, drug, "44425-7"), fallback_texts(data, drug)]
        passages = choose_passages(groups, drug, is_kit(data, drug))
        values.append(join_passages(passages))

    return values
