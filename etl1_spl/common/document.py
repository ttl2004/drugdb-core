import os
import xml.etree.ElementTree as ET

from etl1_spl.common.xml_utils import NS, attr, iso_date, quantity, stable_id, tag, txt

# classCode của một thành phần được coi là hoạt chất
ACTIVE_CLASS = ["ACTIB", "ACTIM", "ACTIR"]

# Mã LOINC của section chứa danh sách sản phẩm
PRODUCT_SECTION = "48780-1"

# Thẻ con cho biết một manufacturedProduct thật sự mang dữ liệu sản phẩm
PRODUCT_CHILD_TAGS = ["name", "ingredient", "asContent", "formCode",
                      "asEntityWithGeneric", "characteristic"]


# Dữ liệu đã bóc tách của một file XML (một tài liệu nhãn thuốc).
class SplDocument:
    def __init__(self):
        self.root = None              # thẻ gốc <document>
        self.category = None          # nhóm: animal / homeopathic / otc / other / prescription
        self.source_path = None       # đường dẫn file, tương đối với thư mục dữ liệu gốc
        self.id = None
        self.set_id = None
        self.version = None
        self.code = None              # thẻ <code> (loại tài liệu)
        self.labeler = None           # tổ chức đứng tên nhãn: (duns, tên, id_root)
        self.org_chain = []           # mọi tổ chức trong cây tác giả: (duns, tên, id_root, tầng)
        self.manufacturer = None      # tổ chức ở tầng sâu nhất của cây tác giả
        self.body = None              # thẻ <structuredBody>; None nếu tài liệu không có
        self.product_section = None   # section sản phẩm 48780-1; None nếu không tìm thấy
        self.products = []            # danh sách Product


# Một sản phẩm (manufacturedProduct) có mã NDC.
class Product:
    def __init__(self):
        self.element = None           # thẻ XML của sản phẩm
        self.ndc = None
        self.drug_id = None
        self.item_seq = None          # thứ tự sản phẩm trong tài liệu
        self.name = None
        self.generic_name = None
        self.form = None              # thẻ <formCode> (dạng bào chế)
        self.route = None             # thẻ <routeCode> (đường dùng)
        self.approval = None          # thẻ <code> của phê duyệt
        self.approval_id = None
        self.dea_schedule = None
        self.marketing_start = None
        self.marketing_end = None
        self.ingredients = []         # danh sách Ingredient
        self.parts = []               # danh sách PartProduct (thành phần của bộ combo)


# Một thành phần (chất) của sản phẩm.
class Ingredient:
    def __init__(self):
        self.unii = None
        self.name = None
        self.class_code = None        # loại thành phần (hoạt chất / tá dược ...)
        self.parent_unii = None       # chất gốc (activeMoiety)
        self.numerator = None         # thẻ tử số của hàm lượng
        self.denominator = None       # thẻ mẫu số của hàm lượng


# Một sản phẩm thành phần trong bộ combo (<part>/<partProduct>).
# Có NDC riêng thì là một thuốc riêng; không có NDC thì drug_id = None
# và cây bao bì của nó được gắn vào thuốc cha.
class PartProduct:
    def __init__(self):
        self.element = None           # thẻ XML của sản phẩm thành phần
        self.part_index = None        # thứ tự <part> trong sản phẩm cha
        self.numerator = None         # số lượng của <part>
        self.denominator = None
        self.route = None
        self.ndc = None
        self.drug_id = None
        self.name = None
        self.form = None
        self.is_new = False           # True: NDC chưa có trong tài liệu, cần ghi thêm dòng thuốc
        self.item_seq = None


# Thành phần có classCode này có phải hoạt chất không.
def is_active(class_code):
    return class_code in ACTIVE_CLASS


# ---------------------------------------------------------------- tổ chức

# Đọc (DUNS, tên, id_root) của một thẻ tổ chức.
def read_org(el):
    id_el = el.find(NS + "id")
    duns = attr(id_el, "extension")
    name = txt(el.find(NS + "name"))
    id_root = attr(id_el, "root")
    return duns, name, id_root


# Duyệt đệ quy các tổ chức con nằm trong holder, thêm vào orgs kèm tầng (depth).
# Một tổ chức có thể có nhiều tổ chức con (đo được tới 18), nên phải duyệt hết,
# không được chỉ lấy con đầu tiên (sẽ bỏ sót 137 DUNS).
def collect_child_orgs(holder, depth, orgs):
    for entity in holder.findall(NS + "assignedEntity"):
        for org in entity.findall(NS + "assignedOrganization"):
            duns, name, id_root = read_org(org)
            if duns:
                orgs.append((duns, name, id_root, depth))

            # đi tiếp xuống tầng sâu hơn
            collect_child_orgs(org, depth + 1, orgs)


# Đọc cây tổ chức trong <author> của tài liệu.
# Trả về (labeler, orgs):
#     labeler = tổ chức ngoài cùng đứng tên nhãn (tầng 1), hoặc None
#     orgs    = mọi tổ chức (duns, tên, id_root, tầng)
def find_organizations(root):
    orgs = []

    node = root.find(NS + "author/" + NS + "assignedEntity")
    if node is None:
        return None, orgs

    outer = node.find(NS + "representedOrganization")
    if outer is None:
        return None, orgs

    # tổ chức ngoài cùng là labeler
    labeler = None
    duns, name, id_root = read_org(outer)
    if duns:
        labeler = (duns, name, id_root)
        orgs.append((duns, name, id_root, 1))

    # các tổ chức con từ tầng 2 trở xuống
    collect_child_orgs(outer, 2, orgs)

    return labeler, orgs


# Nhà sản xuất = tổ chức đầu tiên ở tầng sâu nhất trong cây tác giả.
def find_manufacturer(orgs):
    manufacturer = None

    for org in orgs:
        depth = org[3]
        if manufacturer is None or depth > manufacturer[3]:
            manufacturer = org

    return manufacturer


# ---------------------------------------------------------------- sản phẩm

# manufacturedProduct có thật sự mang dữ liệu sản phẩm không
# (có ít nhất một thẻ con như name, ingredient, formCode ...).
def is_product(el):
    for child in el:
        if tag(child) in PRODUCT_CHILD_TAGS:
            return True
    return False


# Tìm section chứa danh sách sản phẩm (mã LOINC 48780-1); không có thì trả về None.
def find_product_section(root):
    for section in root.iter(NS + "section"):
        code = section.find(NS + "code")
        if code is not None and code.get("code") == PRODUCT_SECTION:
            return section
    return None


# Lập bảng tra "thẻ con -> thẻ cha" trong section sản phẩm.
# Cần vì ElementTree không cho đi ngược lên thẻ cha.
def build_parent_map(section):
    parents = {}
    for parent in section.iter():
        for child in parent:
            parents[id(child)] = parent
    return parents


# Đọc các thành phần (<ingredient>) của một sản phẩm; bỏ thành phần không có mã UNII.
def read_ingredients(product_el):
    result = []

    for ing in product_el.findall(NS + "ingredient"):
        substance = ing.find(NS + "ingredientSubstance")
        if substance is None:
            continue

        unii = attr(substance.find(NS + "code"), "code")
        if not unii:
            continue

        item = Ingredient()
        item.unii = unii
        item.name = txt(substance.find(NS + "name"))
        item.class_code = attr(ing, "classCode")

        # chất gốc nằm trong activeMoiety/activeMoiety/code
        moiety = substance.find(NS + "activeMoiety/" + NS + "activeMoiety/" + NS + "code")
        item.parent_unii = attr(moiety, "code")

        item.numerator, item.denominator = quantity(ing.find(NS + "quantity"))
        result.append(item)

    return result


# Đọc đường dùng, phê duyệt, nhóm kiểm soát DEA, ngày lưu hành của sản phẩm.
# Các thông tin này nằm ở LỚP BỌC NGOÀI của sản phẩm (outer), không nằm trong
# sản phẩm lớp trong (đo được 5.058 trường hợp như vậy).
def read_regulatory(product, outer):
    route_path = NS + "consumedIn/" + NS + "substanceAdministration/" + NS + "routeCode"
    product.route = outer.find(route_path)

    product.approval = outer.find(NS + "subjectOf/" + NS + "approval/" + NS + "code")
    product.approval_id = attr(outer.find(NS + "subjectOf/" + NS + "approval/" + NS + "id"), "extension")

    # nhóm kiểm soát DEA nằm trong policy có classCode DEADrugSchedule
    for policy in outer.findall(NS + "subjectOf/" + NS + "policy"):
        if policy.get("classCode") == "DEADrugSchedule":
            product.dea_schedule = attr(policy.find(NS + "code"), "displayName")

    # ngày bắt đầu / kết thúc lưu hành
    marketing = outer.find(NS + "subjectOf/" + NS + "marketingAct/" + NS + "effectiveTime")
    if marketing is not None:
        product.marketing_start = iso_date(attr(marketing.find(NS + "low"), "value"))
        product.marketing_end = iso_date(attr(marketing.find(NS + "high"), "value"))


# Đọc mọi sản phẩm có NDC trong section sản phẩm, kèm thành phần và bộ combo.
# item_seq đánh số theo thứ tự xuất hiện; sản phẩm thành phần combo có NDC mới
# cũng được đánh số tiếp. Một NDC chỉ được tính là thuốc một lần trong tài liệu.
def read_products(doc_id, section):
    products = []
    parents = build_parent_map(section)
    item_seq = 0
    seen_ndc = set()

    for el in section.iter(NS + "manufacturedProduct"):
        if not is_product(el):
            continue

        # đánh số cả sản phẩm không có NDC (giống bản gốc), nhưng không ghi nó
        item_seq += 1
        ndc = attr(el.find(NS + "code"), "code")
        if not ndc:
            continue
        seen_ndc.add(ndc)

        # thông tin cơ bản của sản phẩm
        product = Product()
        product.element = el
        product.ndc = ndc
        product.drug_id = stable_id(doc_id, ndc)
        product.item_seq = item_seq
        product.name = txt(el.find(NS + "name"))
        product.generic_name = txt(el.find(NS + "asEntityWithGeneric/" + NS + "genericMedicine/" + NS + "name"))
        product.form = el.find(NS + "formCode")

        # lớp bọc ngoài (nếu cha cũng là manufacturedProduct) mang thông tin pháp lý
        outer = parents.get(id(el))
        if outer is None or tag(outer) != "manufacturedProduct":
            outer = el
        read_regulatory(product, outer)

        product.ingredients = read_ingredients(el)

        # bộ combo: mỗi <partProduct> là một sản phẩm thành phần
        part_index = 0
        for part in el.findall(NS + "part"):
            part_index += 1
            numerator, denominator = quantity(part.find(NS + "quantity"))

            # có 319 trường hợp đường dùng nằm trong <part> thay vì trong sản phẩm
            route = part.find(NS + "consumedIn/" + NS + "substanceAdministration/" + NS + "routeCode")

            for part_el in part.findall(NS + "partProduct"):
                item = PartProduct()
                item.element = part_el
                item.part_index = part_index
                item.numerator = numerator
                item.denominator = denominator
                item.route = route
                item.ndc = attr(part_el.find(NS + "code"), "code")

                # có NDC thì là một thuốc riêng
                if item.ndc:
                    item.drug_id = stable_id(doc_id, item.ndc)
                    item.name = txt(part_el.find(NS + "name"))
                    item.form = part_el.find(NS + "formCode")

                    # NDC đã xuất hiện như sản phẩm độc lập (55 trường hợp) thì không ghi lại
                    if item.ndc not in seen_ndc:
                        seen_ndc.add(item.ndc)
                        item_seq += 1
                        item.is_new = True
                        item.item_seq = item_seq

                product.parts.append(item)

        products.append(product)

    return products


# ---------------------------------------------------------------- tài liệu

# Đọc một file XML thành SplDocument.
# File XML lỗi cú pháp sẽ ném ET.ParseError để nơi gọi ghi log và bỏ qua file.
# Tài liệu không có phần thân hoặc không có section sản phẩm thì products rỗng.
def parse_document(category, path, root_dir, log):
    root = ET.parse(path).getroot()

    # thông tin chung của tài liệu
    doc = SplDocument()
    doc.root = root
    doc.category = category
    doc.source_path = os.path.relpath(path, root_dir).replace("\\", "/")
    doc.id = attr(root.find(NS + "id"), "root")
    doc.set_id = attr(root.find(NS + "setId"), "root")
    doc.version = attr(root.find(NS + "versionNumber"), "value")
    doc.code = root.find(NS + "code")

    # tổ chức đứng tên và nhà sản xuất
    doc.labeler, doc.org_chain = find_organizations(root)
    doc.manufacturer = find_manufacturer(doc.org_chain)

    # tài liệu không có phần thân (nonxml) thì dừng ở đây
    doc.body = root.find(NS + "component/" + NS + "structuredBody")
    if doc.body is None:
        return doc

    # sản phẩm nằm trong section 48780-1
    doc.product_section = find_product_section(root)
    if doc.product_section is None:
        log("  ! %s không có section %s" % (path, PRODUCT_SECTION))
        return doc

    doc.products = read_products(doc.id, doc.product_section)
    return doc
