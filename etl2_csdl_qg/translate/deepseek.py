"""
deepseek.py — Gọi API DeepSeek (dạng chat completions). Chỉ file này biết nhà cung cấp LLM;
đổi sang nhà cung cấp khác thì chỉ sửa ở đây.
"""

import json
import time
import urllib.error
import urllib.request

RETRIES = 4          # số lần gửi lại khi lỗi 429 / 5xx / mạng
TIMEOUT = 180        # thời gian chờ mỗi yêu cầu (giây)


# HTTP 401/402: khoá API sai hoặc hết tiền -> phải dừng hẳn, không gửi tiếp.
class ApiKeyError(Exception):
    pass


# Gửi một yêu cầu: prompt là chỉ dẫn hệ thống, text là nội dung cần dịch.
# Trả về câu trả lời của mô hình. Lỗi tạm thời (429, 5xx, mạng) thì chờ rồi thử lại;
# câu trả lời bị cắt hoặc rỗng thì báo lỗi để không lưu bản dịch hỏng.
def call_llm(settings, prompt, text):
    body = {
        "model": settings.model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ],
        "stream": False,
    }
    headers = {
        "Authorization": "Bearer " + settings.api_key,
        "Content-Type": "application/json",
    }
    payload = json.dumps(body).encode("utf-8")

    for attempt in range(1, RETRIES + 1):
        request = urllib.request.Request(settings.api_url, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                result = json.loads(response.read().decode("utf-8"))

            choice = result["choices"][0]
            answer = choice["message"]["content"]

            # câu trả lời phải hoàn chỉnh (finish_reason "stop") và khác rỗng
            if choice.get("finish_reason") != "stop":
                raise ValueError("incomplete answer, finish_reason=%s" % choice.get("finish_reason"))
            if not isinstance(answer, str) or answer.strip() == "":
                raise ValueError("empty answer")

            return answer

        except urllib.error.HTTPError as error:
            # khoá sai / hết tiền: dừng ngay
            if error.code == 401 or error.code == 402:
                raise ApiKeyError("HTTP %d from API (invalid key or no balance)" % error.code)

            # chỉ thử lại khi bị giới hạn tốc độ hoặc lỗi máy chủ
            if error.code != 429 and error.code < 500:
                raise
            if attempt == RETRIES:
                raise

        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == RETRIES:
                raise

        # chờ lâu dần trước khi thử lại: 2, 4, 8 giây
        time.sleep(2 ** attempt)
