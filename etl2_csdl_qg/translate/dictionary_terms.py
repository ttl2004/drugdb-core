import csv
import json
import os

from etl2_csdl_qg.common.dictionary import read_dictionary_file
from etl2_csdl_qg.constants import DICTIONARY_NAMES
from etl2_csdl_qg.translate.deepseek import ApiKeyError, call_llm
from etl2_csdl_qg.translate.prompts import PROMPTS

BATCH_SIZE = 100     # số từ gửi trong một yêu cầu
TERM_COLUMNS = ["tu_dien", "tieng_anh", "tieng_viet", "so_dong"]


# Bỏ dòng mở ```json (hoặc ```) và dấu ``` đóng nếu mô hình bọc câu trả lời trong khối code.
def strip_code_fence(text):
    text = text.strip()
    if not text.startswith("```"):
        return text

    newline = text.find("\n")
    if newline == -1:
        return ""

    text = text[newline + 1:].rstrip()
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


# Đọc câu trả lời (mảng JSON) thành danh sách bản dịch.
# Sai số phần tử, hoặc có phần tử rỗng / không phải chuỗi thì báo lỗi.
def parse_answer(answer, expected_count):
    items = json.loads(strip_code_fence(answer))
    if not isinstance(items, list) or len(items) != expected_count:
        raise ValueError("expected a JSON array of %d items" % expected_count)

    result = []
    for item in items:
        if not isinstance(item, str) or item.strip() == "":
            raise ValueError("empty or non-string item in answer")
        result.append(item.strip())

    return result


# Ghi thêm các cặp (tiếng Anh, tiếng Việt) vào cuối file từ điển name.csv (tạo file nếu chưa có).
def append_to_dictionary(dictionary_dir, name, english_words, vietnamese_words):
    path = os.path.join(dictionary_dir, name + ".csv")

    # file chưa có thì tạo với dòng tiêu đề
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(["tieng_anh", "tieng_viet"])

    # dòng cuối file chưa xuống dòng thì thêm xuống dòng trước khi ghi tiếp
    with open(path, "rb") as f:
        content = f.read()

    with open(path, "a", encoding="utf-8", newline="") as f:
        if content and not content.endswith(b"\n"):
            f.write("\r\n")

        writer = csv.writer(f)
        for i in range(len(english_words)):
            writer.writerow([english_words[i], vietnamese_words[i]])


# Đọc dictionary_terms.csv thành danh sách dict.
def read_terms(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# Đếm số từ trong dictionary_terms.csv còn trống bản dịch (cần gọi API để dịch).
def count_empty_terms(term_rows):
    count = 0
    for row in term_rows:
        if row["tieng_viet"].strip() == "":
            count += 1
    return count


# Ghi lại dictionary_terms.csv (ra file tạm rồi thay file cũ, để không hỏng file nếu bị dừng).
def write_terms(path, rows):
    temp_path = path + ".tmp"

    with open(temp_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TERM_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    os.replace(temp_path, path)


# Bổ sung bản dịch cho một từ điển (name). term_rows là các dòng của dictionary_terms.csv;
# bản dịch mới được điền vào term_rows và ghi lại file ngay sau mỗi nhóm thành công,
# để lần chạy sau không phải dịch lại. Trả về số liệu {"copied", "empty", "translated", "failed"}.
def translate_dictionary(settings, name, term_rows, terms_path, log):
    existing = read_dictionary_file(os.path.join(settings.dictionary_dir, name + ".csv"))

    # chia các từ của từ điển này thành: cần dịch / đã gõ tay
    to_translate = []
    typed_words = []
    typed_translations = []
    for row in term_rows:
        if row["tu_dien"] != name:
            continue

        if row["tieng_viet"].strip() == "":
            to_translate.append(row)
        elif row["tieng_anh"] not in existing:
            typed_words.append(row["tieng_anh"])
            typed_translations.append(row["tieng_viet"].strip())

    # bản dịch gõ tay: chép thẳng vào file từ điển
    if typed_words:
        append_to_dictionary(settings.dictionary_dir, name, typed_words, typed_translations)

    # từ còn trống: gửi LLM theo từng nhóm
    translated = 0
    failed = 0
    for start in range(0, len(to_translate), BATCH_SIZE):
        batch = to_translate[start:start + BATCH_SIZE]

        english_words = []
        for row in batch:
            english_words.append(row["tieng_anh"])

        try:
            answer = call_llm(settings, PROMPTS[name], json.dumps(english_words, ensure_ascii=False))
            vietnamese_words = parse_answer(answer, len(english_words))
        except ApiKeyError:
            raise
        except Exception as error:
            log("  WARNING: %s: request failed: %s" % (name, ascii(str(error))))
            failed += len(english_words)
            continue

        # lưu bản dịch vào file từ điển và dictionary_terms.csv
        append_to_dictionary(settings.dictionary_dir, name, english_words, vietnamese_words)
        for i in range(len(batch)):
            batch[i]["tieng_viet"] = vietnamese_words[i]
        write_terms(terms_path, term_rows)

        translated += len(english_words)

    log("  %-11s gõ tay %d | trống %d, đã dịch %d, lỗi %d"
        % (name, len(typed_words), len(to_translate), translated, failed))

    return {"copied": len(typed_words), "empty": len(to_translate),
            "translated": translated, "failed": failed}


# Bổ sung bản dịch cho cả 4 từ điển. Trả về {tên từ điển: số liệu}.
# Khoá API sai hoặc hết tiền thì ném ApiKeyError để dừng cả bước.
def translate_missing(settings, terms_path, log):
    term_rows = read_terms(terms_path)

    results = {}
    for name in DICTIONARY_NAMES:
        results[name] = translate_dictionary(settings, name, term_rows, terms_path, log)

    return results
