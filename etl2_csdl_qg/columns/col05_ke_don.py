from etl2_csdl_qg.constants import PRESCRIPTION_DOC_TYPES

HEADER = "Là thuốc kê đơn (*)"


# Giá trị cột cho mọi thuốc, theo thứ tự data.drugs.
def build(data):
    values = []
    for drug in data.drugs:
        doc_type = data.documents[drug["document_id"]]["doc_code_display"]

        if doc_type in PRESCRIPTION_DOC_TYPES:
            values.append("Có")
        else:
            values.append("Không")

    return values
