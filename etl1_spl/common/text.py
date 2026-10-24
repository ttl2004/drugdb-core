import xml.etree.ElementTree as ET

from etl1_spl.common.xml_utils import NS, tag


# Nối toàn bộ chữ trong một thẻ và các thẻ con của nó.
# <br/> thành xuống dòng, hình ảnh thành " [hình] ", chú thích cuối trang bị bỏ.
def inline_text(node):
    parts = []

    # chữ nằm ngay đầu thẻ
    if node.text:
        parts.append(node.text)

    for child in node:
        name = tag(child)

        # thẻ đặc biệt thì thay bằng ký hiệu, thẻ thường thì lấy chữ bên trong
        if name == "br":
            parts.append("\n")
        elif name == "renderMultiMedia":
            parts.append(" [hình] ")
        elif name == "footnote":
            parts.append("")
        else:
            parts.append(inline_text(child))

        # chữ nằm sau thẻ con, trước thẻ con kế tiếp
        if child.tail:
            parts.append(child.tail)

    return "".join(parts)


# Gộp mọi khoảng trắng / xuống dòng liên tiếp thành một dấu cách.
def clean_spaces(text):
    return " ".join(text.split())


# Duyệt các thẻ con của node, thêm mỗi khối văn bản vào danh sách blocks:
# đoạn văn -> một dòng, mục danh sách -> "- ...", hàng bảng -> "ô 1 | ô 2 | ...".
# Thẻ khác thì đi tiếp vào bên trong.
def collect_blocks(node, blocks):
    for child in node:
        name = tag(child)

        # đoạn văn
        if name == "paragraph":
            line = clean_spaces(inline_text(child))
            if line:
                blocks.append(line)

        # danh sách: mỗi mục một dòng có gạch đầu dòng
        elif name == "list":
            for item in child.findall(NS + "item"):
                line = clean_spaces(inline_text(item))
                if line:
                    blocks.append("- " + line)

        # bảng: mỗi hàng một dòng, các ô (khác rỗng) nối bằng " | "
        elif name == "table":
            for row in child.iter(NS + "tr"):
                cells = []
                for cell in row:
                    if tag(cell) == "td" or tag(cell) == "th":
                        value = clean_spaces(inline_text(cell))
                        if value:
                            cells.append(value)
                if cells:
                    blocks.append(" | ".join(cells))

        # thẻ bao ngoài khác: tìm tiếp bên trong
        else:
            collect_blocks(child, blocks)


# Chuyển thẻ <text> của mục nhãn thành văn bản thuần (để tìm kiếm, tạo vector, dịch).
# Không có nội dung thì trả về None.
def to_plain(text_el):
    if text_el is None:
        return None

    blocks = []
    collect_blocks(text_el, blocks)

    result = "\n".join(blocks).strip()
    if result == "":
        return None
    return result


# Lấy chuỗi XML gốc của mọi thẻ con bên trong một thẻ, giữ nguyên định dạng (cột text_xml).
# Không có nội dung thì trả về None.
def inner_xml(el):
    if el is None:
        return None

    parts = []
    for child in el:
        parts.append(ET.tostring(child, encoding="unicode"))

    result = "".join(parts).strip()
    if result == "":
        return None
    return result
