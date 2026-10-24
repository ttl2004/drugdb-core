import csv
import json
import os

from etl2_csdl_qg.constants import ACTIVE_CLASS_CODES, EXCLUDED_DOC_TYPES

# Văn bản nhãn có ô rất dài, nâng giới hạn kích thước ô của module csv lên 1 GB
csv.field_size_limit(1073741824)


# Dữ liệu đầu vào của ETL 2, đã sắp xếp sẵn để tra cứu nhanh.
class InputData:
    def __init__(self):
        self.dictionary = None              # từ điển Anh -> Việt (Dictionary)
        self.drugs = []                     # các thuốc được xuất (mỗi thuốc một dòng đầu ra)
        self.documents = {}                 # document_id -> dòng label_document
        self.ingredient_names = {}          # unii -> tên chất
        self.active_ingredients = {}        # drug_id -> các dòng drug_ingredient là hoạt chất
        self.packages = {}                  # drug_id -> các dòng drug_package
        self.sections = {}                  # document_id -> cây mục nhãn (từ label_section.jsonl)
        self.kit_documents = set()          # document_id của tài liệu bộ kit
        self.cache = {}                     # kết quả đã tính, theo (document_id, tên phép tính)


# Đọc cả một file CSV thành danh sách dict (mỗi dòng một dict).
def read_csv(folder, file_name):
    with open(os.path.join(folder, file_name), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# Khoá sắp xếp: thứ tự hiển thị của thành phần trong thuốc.
def display_order_of(row):
    return int(row["display_order"])


# Gom các dòng theo drug_id: {drug_id: [dòng, ...]}, giữ thứ tự trong file.
def group_by_drug(rows):
    groups = {}
    for row in rows:
        drug_id = row["drug_id"]
        if drug_id not in groups:
            groups[drug_id] = []
        groups[drug_id].append(row)
    return groups


# Hai thuốc trùng NDC: thuốc mới (new) có được ưu tiên hơn thuốc đang giữ (old) không.
# Thứ tự xét: tài liệu mới hơn -> có hoạt chất -> version cao hơn -> không phải thành phần kit.
def is_preferred(new, old, documents, kit_parts):
    new_doc = documents[new["document_id"]]
    old_doc = documents[old["document_id"]]

    # tài liệu có hiệu lực mới hơn
    if new_doc["effective_time"] != old_doc["effective_time"]:
        return new_doc["effective_time"] > old_doc["effective_time"]

    # thuốc có hoạt chất
    if new["has_active"] != old["has_active"]:
        return new["has_active"] == "1"

    # phiên bản tài liệu cao hơn
    if int(new_doc["version"]) != int(old_doc["version"]):
        return int(new_doc["version"]) > int(old_doc["version"])

    # thuốc độc lập được ưu tiên hơn thành phần của bộ kit
    new_is_part = new["id"] in kit_parts
    old_is_part = old["id"] in kit_parts
    return old_is_part and not new_is_part


# Chọn các thuốc được xuất: bỏ thuốc thú y / thực phẩm chức năng (ngoài phạm vi CSDL Dược);
# NDC trùng thì chỉ giữ một thuốc theo is_preferred. Giữ thứ tự gặp NDC lần đầu.
def select_drugs(all_drugs, documents, kit_parts):
    by_ndc = {}

    for drug in all_drugs:
        doc = documents.get(drug["document_id"])
        if doc is None:
            continue

        # ngoài phạm vi
        if doc["source_category"] == "animal":
            continue
        if doc["doc_code_display"] in EXCLUDED_DOC_TYPES:
            continue

        # NDC mới thì giữ; NDC đã có thì thay nếu thuốc này được ưu tiên hơn
        old = by_ndc.get(drug["ndc"])
        if old is None or is_preferred(drug, old, documents, kit_parts):
            by_ndc[drug["ndc"]] = drug

    return list(by_ndc.values())


# Đọc các CSV của ETL 1 trong input_dir thành InputData.
# Cây mục nhãn (label_section.jsonl) chỉ đọc cho các tài liệu có thuốc được xuất, để đỡ tốn bộ nhớ.
def load_input(input_dir, dictionary):
    data = InputData()
    data.dictionary = dictionary

    # tài liệu
    for row in read_csv(input_dir, "label_document.csv"):
        data.documents[row["id"]] = row

    # tên chất
    for row in read_csv(input_dir, "ingredient.csv"):
        data.ingredient_names[row["unii"]] = row["name"]

    # hoạt chất của từng thuốc, sắp theo display_order
    active_rows = []
    for row in read_csv(input_dir, "drug_ingredient.csv"):
        if row["class_code"] in ACTIVE_CLASS_CODES:
            active_rows.append(row)
    data.active_ingredients = group_by_drug(active_rows)
    for drug_id in data.active_ingredients:
        data.active_ingredients[drug_id] = sorted(data.active_ingredients[drug_id], key=display_order_of)

    # bao bì của từng thuốc
    data.packages = group_by_drug(read_csv(input_dir, "drug_package.csv"))

    all_drugs = read_csv(input_dir, "drug_knowledge.csv")

    # bộ kit: thuốc là bộ cha hoặc thành phần trong drug_part
    kit_parts = set()
    kit_drugs = set()
    for row in read_csv(input_dir, "drug_part.csv"):
        kit_parts.add(row["part_drug_id"])
        kit_drugs.add(row["part_drug_id"])
        kit_drugs.add(row["parent_drug_id"])

    # tài liệu kit = tài liệu chứa thuốc thuộc bộ kit
    for drug in all_drugs:
        if drug["id"] in kit_drugs:
            data.kit_documents.add(drug["document_id"])

    data.drugs = select_drugs(all_drugs, data.documents, kit_parts)

    # cây mục nhãn của các tài liệu cần dùng
    needed_documents = set()
    for drug in data.drugs:
        needed_documents.add(drug["document_id"])

    with open(os.path.join(input_dir, "label_section.jsonl"), encoding="utf-8") as f:
        for line in f:
            document = json.loads(line)
            if document["document_id"] in needed_documents:
                data.sections[document["document_id"]] = document["sections"]

    return data
