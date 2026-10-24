"""
prompts.py — Chỉ dẫn (prompt) gửi cho LLM khi dịch từng từ điển.

Mỗi yêu cầu gửi một mảng JSON các từ tiếng Anh; mô hình phải trả về mảng JSON
bản dịch cùng độ dài, cùng thứ tự.
"""

ROUTE = """You translate drug route-of-administration terms (FDA SPL route names) into Vietnamese pharmacy terminology, as used on Vietnamese drug registrations.
Examples: ORAL -> Uống; INTRAVENOUS -> Tiêm tĩnh mạch; TOPICAL -> Dùng ngoài; OPHTHALMIC -> Nhỏ mắt; SUBLINGUAL -> Ngậm dưới lưỡi.
Every answer must start with an action verb: Uống, Tiêm, Dùng, Nhỏ, Đặt, Ngậm, Hít, Dán, Rửa.
Injection routes: "Tiêm" + site (e.g. "Tiêm bắp"). If a route covers several dosage forms (drops, sprays, gels...), use the general "Dùng ..." form instead of a single action.
Write each term with only its first letter capitalized.
The user sends a JSON array of English terms. Reply with ONLY a JSON array of Vietnamese strings, same length and same order. No explanation."""

PACKAGE = """You translate drug packaging/container types (FDA SPL package form names) into Vietnamese pharmacy terminology.
Answer with a short lowercase Vietnamese noun, as used in phrases like "Hộp 3 vỉ x 10 viên".
Examples: CARTON -> hộp; BOTTLE -> chai; BLISTER PACK -> vỉ; VIAL -> lọ; TUBE -> tuýp; POUCH -> túi.
The user sends a JSON array of English terms. Reply with ONLY a JSON array of Vietnamese strings, same length and same order. No explanation."""

COUNT_UNIT = """You get the first word(s) of a drug dosage form name (FDA SPL, e.g. TABLET, PATCH, SPRAY, INJECTION). Give the lowercase Vietnamese counting unit used when counting that dosage form in a package description such as "Hộp 3 vỉ x 10 viên".
Examples: TABLET -> viên; CAPSULE -> viên; PATCH -> miếng; KIT -> bộ; GRANULE -> gói; SPRAY -> liều xịt.
The user sends a JSON array of English terms. Reply with ONLY a JSON array of Vietnamese strings, same length and same order. No explanation."""

UNIT = """You convert UCUM unit codes used for drug strengths and quantities into the short unit text used on Vietnamese drug labels.
Keep standard international symbols unchanged (mg -> mg, mL -> mL, g -> g, kg -> kg, L -> L, mCi -> mCi).
Examples: ug -> mcg; [iU] -> IU; meq -> mEq; h -> giờ; d -> ngày; [hp_X] -> X; [CFU] -> CFU; U -> U.
The user sends a JSON array of unit codes. Reply with ONLY a JSON array of strings, same length and same order. No explanation."""

# tên từ điển -> prompt
PROMPTS = {
    "duong_dung": ROUTE,
    "bao_bi": PACKAGE,
    "don_vi_dem": COUNT_UNIT,
    "don_vi": UNIT,
}
