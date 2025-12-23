# import pandas as pd
# import unicodedata

# # =========================
# # CẤU HÌNH CƠ BẢN
# # =========================

# INPUT_EXCEL = "../merged_books.xlsx"
# OUTPUT_EXCEL = "merged_books_with_main_category.xlsx"

# # Sau khi chạy xong sẽ có cột:
# # - main_category_suggested  (thể loại chuẩn tiếng Việt)
# # - category_name_new        (sẽ dùng để update category_name trong DB)
# # - format_suggested
# # - language_display


# # =========================
# # HÀM TIỆN ÍCH
# # =========================

# def strip_accents(s: str) -> str:
#     """Bỏ dấu tiếng Việt để so khớp từ khóa dễ hơn."""
#     if not isinstance(s, str):
#         return ""
#     s = unicodedata.normalize("NFD", s)
#     return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


# def normalize_text(*parts) -> str:
#     """
#     Ghép nhiều đoạn text (title, description, categories...) rồi:
#     - lower
#     - bỏ dấu
#     """
#     joined = " ".join(p for p in parts if isinstance(p, str))
#     return strip_accents(joined).lower()


# def split_categories(cat_str: str):
#     """Tách chuỗi categories 'a, b, c' -> ['a','b','c']"""
#     if not isinstance(cat_str, str):
#         return []
#     return [c.strip() for c in cat_str.split(",") if c.strip()]


# # =========================
# # BỘ THỂ LOẠI CHÍNH (CHỈ TIẾNG VIỆT)
# # =========================

# MAIN_CATEGORY_KEYWORDS = [
#     # (Tên thể loại chuẩn tiếng Việt, list từ khóa (không dấu, lower))
#     ("Truyện tranh", [
#         "truyen tranh", "comic", "comics", "manga", "manhwa", "manhua",
#         "graphic novel", "strips"
#     ]),
#     ("Thiếu nhi", [
#         "thieu nhi", "nhi dong", "tre em", "children", "kids",
#         "juvenile fiction", "juvenile nonfiction", "young adult fiction",
#         "young adult nonfiction", "thieu nhi", "nhi dong", "thieu nien", "thieu nu",
#         "truyen thieu nhi", "truyen ke cho be", "ke chuyen cho be",
#         "ke chuyen em nghe", "hoang tu be", "co tich", "truyen co tich",
#         "truyen dong thoai", "cau chuyen ve", "chu be",
#         "hoang tu", "con tho", "meo con", "nguoi tuyet nho", "kid",
#         "children", "thieu nhi song ngu"
#     ]),
#     ("Kinh dị", [
#         "kinh di", "horror", "am anh", "ma am", "ma quai", "thriller", "kinh di", "am anh", "ma quai", "ma mi", "ghost", "horror",
#         "truyen ma", "ngoi nha ma", "quai vat", "am khi", "ladder of horror"
#     ]),
#     ("Trinh thám", [
#         "trinh tham", "detective", "mystery", "an mang", "hinh su", "crime", "trinh tham", "hinh su", "an mang", "vu an", "thanh tra",
#         "than tham", "tham tu", "detective", "mystery", "crime",
#         "kho tang trinh tham", "ho so vu an"
#     ]),
#     ("Ngôn tình", [
#         "ngon tinh", "romance", "ngon tinh", "tieu thuyet tinh cam", "tinh yeu", "tinh cam",
#         "yeu em", "yeu anh", "tinh su", "lang man"
#     ]),
#     ("Tiểu thuyết", [
#         "tieu thuyet", "novel", "fiction"
#     ]),
#     ("Đam mỹ", [
#         "dam my", "danmei", "boys love", "bl "
#     ]),
#     ("Tiên hiệp", [
#         "tien hiep", "tien kiem", "xianxia"
#     ]),
#     ("Xuyên không", [
#         "xuyen khong", "xuyen qua", "trong sinh", "time travel"
#     ]),
#     ("Võng du", [
#         "vong du", "game online", "mmorpg", "game thu"
#     ]),
#     ("Kiếm hiệp", [
#         "kiem hiep", "vo hiep", "wuxia"
#     ]),
#     ("Kỹ năng sống", [
#         "ky nang song", "self-help", "self help", "thanh cong", "lam giau",
#         "thoi quen", "mindset", "phat trien ban than", "phat trien ca nhan"
#     ]),
#     ("Kinh doanh - Kinh tế", [
#         "kinh doanh", "business", "marketing", "ban hang", "sales",
#         "thuong hieu", "brand", "dau tu", "tai chinh", "chung khoan",
#         "bat dong san", "khoi nghiep", "start up", "startup", "economics",
#         "kinh te"
#     ]),
#     ("Khoa học tự nhiên", [
#         "khoa hoc", "science", "vat ly", "hoa hoc", "sinh hoc", "thi nghiem",
#         "vu tru", "astronomy", "sinh thai", "bao ton"
#     ]),
#     ("Công nghệ - Kỹ thuật", [
#         "cong nghe thong tin", "cntt", "lap trinh", "coding", "python",
#         "java", "tri tue nhan tao", "ai ", "machine learning",
#         "khoa hoc du lieu", "data science", "engineering", "ky thuat",
#         "cong nghe"
#     ]),
#     ("Giáo dục - Giáo trình", [
#         "giao trinh", "sach giao khoa", "bai tap", "on luyen", "luyen thi",
#         "de thi", "trac nghiem", "ngu phap", "bai tap nang cao",
#         "tham khao hoc", "test prep", "study aids", "education"
#     ]),
#     ("Lịch sử", [
#         "lich su", "history", "chien tranh", "war", "cach mang", "trieu dai",
#         "dien bien phu", "viet nam khang chien", "indochinese war"
#     ]),
#     ("Tâm lý học", [
#         "tam ly", "psychology", "fomo", "dopamine", "cam xuc", "stress",
#         "tram cam", "tu ky", "tam ly hoc"
#     ]),
#     ("Hồi ký - Tự truyện", [
#         "hoi ky", "hoi ki", "tu truyen", "memoir", "nhat ky", "nhat ki"
#     ]),
#     ("Văn học - Thơ - Tản văn", [
#         "tan van", "tuy but", "essay", "poetry", "tho", "thơ",
#         "van chuong", "van hoc"
#     ]),
#     ("Tôn giáo - Tâm linh", [
#         "phat giao", "phat hoc", "buddhism", "thien", "thien tong",
#         "dao phat", "ton giao", "religion", "cong giao", "thien chua",
#         "kito", "kito giao", "kitô"
#     ]),
#     ("Triết học", [
#         "triet hoc", "philosophy"
#     ]),
#     ("Khoa học xã hội", [
#         "social science", "social sciences", "xa hoi hoc", "sociology",
#         "nhan hoc", "anthropology", "khoa hoc xa hoi"
#     ]),
# ]

# # Map từ category gốc (nhiều loại lặt vặt) → THỂ LOẠI CHUẨN TIẾNG VIỆT
# CANONICAL_CATEGORY_MAP = {
#     # --- category tiếng Anh map sang tiếng Việt ---
#     "Juvenile Fiction": "Thiếu nhi",
#     "Juvenile Nonfiction": "Thiếu nhi",
#     "Young Adult Fiction": "Thiếu nhi",
#     "Young Adult Nonfiction": "Thiếu nhi",

#     "Comics & Graphic Novels": "Truyện tranh",
#     "Comic books": "Truyện tranh",
#     "Comic books, strips": "Truyện tranh",

#     "Fiction": "Tiểu thuyết",
#     "Mystery fiction": "Trinh thám",
#     "Detective and mystery stories": "Trinh thám",

#     "Family & Relationships": "Kỹ năng sống",
#     "Self-Help": "Kỹ năng sống",
#     "Mind & Spirit": "Kỹ năng sống",

#     "Business & Economics": "Kinh doanh - Kinh tế",
#     "Finance": "Kinh doanh - Kinh tế",
#     "Economics": "Kinh doanh - Kinh tế",
#     "Investment": "Kinh doanh - Kinh tế",
#     "Investments": "Kinh doanh - Kinh tế",
#     "Stock exchanges": "Kinh doanh - Kinh tế",
#     "Real estate business": "Kinh doanh - Kinh tế",
#     "Marketing": "Kinh doanh - Kinh tế",
#     "Sales management": "Kinh doanh - Kinh tế",
#     "Entrepreneurship": "Kinh doanh - Kinh tế",
#     "New business enterprises": "Kinh doanh - Kinh tế",
#     "Industrial management": "Kinh doanh - Kinh tế",
#     "Management": "Kinh doanh - Kinh tế",

#     "Science": "Khoa học tự nhiên",
#     "Biology": "Khoa học tự nhiên",
#     "Physics": "Khoa học tự nhiên",
#     "Chemistry": "Khoa học tự nhiên",
#     "Natural history": "Khoa học tự nhiên",

#     "Technology & Engineering": "Công nghệ - Kỹ thuật",
#     "Computers": "Công nghệ - Kỹ thuật",
#     "Computer programming": "Công nghệ - Kỹ thuật",
#     "Information technology": "Công nghệ - Kỹ thuật",

#     "Education": "Giáo dục - Giáo trình",
#     "Study Aids": "Giáo dục - Giáo trình",
#     "Foreign Language Study": "Giáo dục - Giáo trình",

#     "History": "Lịch sử",

#     "Religion": "Tôn giáo - Tâm linh",
#     "Religions": "Tôn giáo - Tâm linh",

#     "Philosophy": "Triết học",

#     "Social Science": "Khoa học xã hội",
#     "Social sciences": "Khoa học xã hội",
#     "Sociology": "Khoa học xã hội",
#     "Anthropology": "Khoa học xã hội",

#     "Literary Collections": "Văn học - Thơ - Tản văn",
#     "Literary Criticism": "Văn học - Thơ - Tản văn",
#     "Poetry": "Văn học - Thơ - Tản văn",

#     # --- category tiếng Việt giữ nguyên nhưng map về label chuẩn ---
#     "Thiếu nhi": "Thiếu nhi",
#     "Truyện tranh": "Truyện tranh",
#     "Kinh dị": "Kinh dị",
#     "Trinh thám": "Trinh thám",
#     "Ngôn tình": "Ngôn tình",
#     "Tiểu thuyết": "Tiểu thuyết",
#     "Đam mỹ": "Đam mỹ",
#     "Tiên hiệp": "Tiên hiệp",
#     "Xuyên không": "Xuyên không",
#     "Võng du": "Võng du",
#     "Kiếm hiệp": "Kiếm hiệp",

#     "Kỹ năng sống": "Kỹ năng sống",
#     "Kỹ năng sống / Self-Help": "Kỹ năng sống",

#     "Kinh tế - Tài chính": "Kinh doanh - Kinh tế",
#     "Kinh doanh": "Kinh doanh - Kinh tế",

#     "Giáo dục": "Giáo dục - Giáo trình",
#     "Giáo trình": "Giáo dục - Giáo trình",
#     "Giáo dục / Giáo trình": "Giáo dục - Giáo trình",

#     "Lịch sử": "Lịch sử",

#     "Tâm lí học": "Tâm lý học",
#     "Tâm lý học": "Tâm lý học",

#     "Hồi kí": "Hồi ký - Tự truyện",
#     "Hồi ký": "Hồi ký - Tự truyện",

#     "Văn học": "Văn học - Thơ - Tản văn",
#     "Thơ ca": "Văn học - Thơ - Tản văn",
#     "Văn học / Thơ / Tản văn": "Văn học - Thơ - Tản văn",

#     "Triết học": "Triết học",

#     "Tôn giáo": "Tôn giáo - Tâm linh",
#     "Tôn giáo / Tâm linh": "Tôn giáo - Tâm linh",

#     "Văn Hoá - Xã Hội": "Khoa học xã hội",
# }


# # =========================
# # NHẬN DIỆN THỂ LOẠI CHÍNH
# # =========================

# def get_main_cat_from_existing_tags(cat_list):
#     """
#     Từ list tag hiện có (categories đã tách),
#     thử tìm xem có tag nào thuộc CANONICAL_CATEGORY_MAP không.
#     """
#     for raw in cat_list:
#         key = raw.strip()
#         # thử đúng y chang
#         if key in CANONICAL_CATEGORY_MAP:
#             return CANONICAL_CATEGORY_MAP[key]

#         # thử bỏ hoa/thường
#         key_lower = key.lower()
#         for k in CANONICAL_CATEGORY_MAP.keys():
#             if k.lower() == key_lower:
#                 return CANONICAL_CATEGORY_MAP[k]

#     return None


# def get_main_cat_from_text(text_norm: str):
#     """
#     Dựa vào text (title + description + categories, đã bỏ dấu và lower)
#     quét keywords để đoán thể loại chính.
#     """
#     for cat_name, keywords in MAIN_CATEGORY_KEYWORDS:
#         for kw in keywords:
#             if kw in text_norm:
#                 return cat_name
#     return None


# def infer_main_category(row):
#     """
#     Hàm chính để suy ra main_category_suggested cho từng sách.
#     Ưu tiên:
#       1) Category hiện có (via CANONICAL_CATEGORY_MAP)
#       2) Tên sách + mô tả + categories (via MAIN_CATEGORY_KEYWORDS)
#       3) Nếu vẫn chưa có -> 'Khác'
#     """
#     title = row.get("title", "")
#     desc = row.get("description", "")
#     cat_str = row.get("categories", "")

#     cat_list = split_categories(cat_str)

#     # 1) Thử từ categories hiện tại
#     main_cat = get_main_cat_from_existing_tags(cat_list)
#     if main_cat:
#         return main_cat

#     # 2) Dùng title + description + categories -> text_norm
#     text_norm = normalize_text(title, desc, cat_str)
#     main_cat = get_main_cat_from_text(text_norm)
#     if main_cat:
#         return main_cat

#     # 3) Không đoán ra
#     return "Khác"


# # =========================
# # FORMAT, LANGUAGE
# # =========================

# FORMAT_KEYWORDS = {
#     "Epub": ["epub"],
#     "Pdf": ["pdf"],
#     "Mobi": ["mobi"],
#     "Azw3": ["azw3"],
#     "Cbz": ["cbz"],
#     "eBook": ["ebook", "e-book", "sach dien tu", "sách điện tử"],
#     "CD-ROMs": ["cd-rom", "cd rom", "cdrom"],
#     "Audiobook": ["audiobook", "audio book", "sach noi", "sách nói", "mp3"],
# }

# LANGUAGE_CODE_MAP = {
#     "vi": "Vietnamese",
#     "en": "English",
#     "fr": "French",
#     "de": "German",
#     "ja": "Japanese",
#     "zh": "Chinese",
#     "ko": "Korean",
#     "ru": "Russian",
# }


# def infer_format(row):
#     text_norm = normalize_text(row.get("title", ""), row.get("categories", ""))
#     for fmt, kws in FORMAT_KEYWORDS.items():
#         for kw in kws:
#             if kw in text_norm:
#                 return fmt
#     return None


# def infer_language(row):
#     lang_code = str(row.get("language", "")).strip().lower()
#     if lang_code in LANGUAGE_CODE_MAP:
#         return LANGUAGE_CODE_MAP[lang_code]
#     # fallback nhỏ: nếu title gần như toàn ASCII -> đoán English
#     title = str(row.get("title", "") or "")
#     if title and all(ord(ch) < 128 for ch in title):
#         return "English"
#     # default
#     return "Vietnamese"


# # =========================
# # CHẠY SCRIPT
# # =========================

# def main():
#     print("Đọc file Excel:", INPUT_EXCEL)
#     df = pd.read_excel(INPUT_EXCEL)

#     # Thể loại chính (chuẩn tiếng Việt)
#     print("Đang suy luận main_category_suggested từ title + categories...")
#     df["main_category_suggested"] = df.apply(infer_main_category, axis=1)

#     # Category_name mới = main_category_suggested (dùng để update DB)
#     df["category_name_new"] = df["main_category_suggested"]

#     # Format (Epub/Pdf/Mobi/...)
#     print("Đang suy luận format_suggested...")
#     df["format_suggested"] = df.apply(infer_format, axis=1)

#     # Ngôn ngữ hiển thị
#     print("Đang suy luận language_display...")
#     df["language_display"] = df.apply(infer_language, axis=1)

#     # Xuất ra Excel để kiểm tra bằng tay
#     print("Ghi ra:", OUTPUT_EXCEL)
#     df.to_excel(OUTPUT_EXCEL, index=False)
#     print("Xong! Mở file", OUTPUT_EXCEL,
#           "để kiểm tra / chỉnh tay thêm nếu cần.")


# if __name__ == "__main__":
#     main()


import pandas as pd
import unicodedata
import re

# =========================
# CẤU HÌNH CƠ BẢN
# =========================

INPUT_EXCEL = "../merged_books.xlsx"
OUTPUT_EXCEL = "merged_books_with_manual_category.xlsx"
MANUAL_CSV = "manual_title_categories.csv"  # file bạn đã tạo

TITLE_COL = "title"  # tên cột tiêu đề trong Excel
COVER_URL_COL = "cover_url"


# =========================
# HÀM TIỆN ÍCH
# =========================

def strip_accents(s: str) -> str:
    """Bỏ dấu tiếng Việt + chuẩn hóa 'đ' -> 'd'."""
    if not isinstance(s, str):
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    return s


def normalize_title_for_lookup(title: str) -> str:
    """
    Chuẩn hóa title để khớp với cột title_norm trong manual_title_categories.csv:

    - bỏ dấu
    - lower
    - thay mọi chuỗi ký tự KHÔNG phải [a-z0-9] thành 1 space
    - gom nhiều space thành 1
    - ví dụ: "Học Công Nghệ..., Rồi Làm Gì?" -> "hoc cong nghe thong tin roi lam gi"
             "1/14"                          -> "1 14"
    """
    if not isinstance(title, str):
        return ""
    s = strip_accents(title).lower()
    # thay tất cả ký tự không phải a-z0-9 thành space
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()    # gom space
    return s


def load_manual_mapping(csv_path: str) -> dict:
    """
    Đọc file manual_title_categories.csv và trả về dict:
        {norm_key: main_category_manual}

    norm_key được chuẩn hóa lại bằng cùng hàm normalize_title_for_lookup,
    để tránh lệch format so với file merged_books.xlsx.
    Đồng thời KHÔNG lấy trùng title_norm: gặp lại key thì bỏ qua.
    """
    print("Đọc file mapping:", csv_path)
    df_map = pd.read_csv(csv_path)

    required_cols = {"title", "main_category_manual"}
    if not required_cols.issubset(df_map.columns):
        raise ValueError(
            f"File {csv_path} phải có ít nhất các cột: {', '.join(required_cols)}. "
            f"Các cột hiện có: {', '.join(df_map.columns)}"
        )

    has_title_norm = "title_norm" in df_map.columns

    mapping = {}
    dup_skipped = 0
    usable_rows = 0

    for _, row in df_map.iterrows():
        # Ưu tiên dùng title_norm nếu có, không thì dùng title gốc
        if has_title_norm and pd.notna(row["title_norm"]) and str(row["title_norm"]).strip():
            base = str(row["title_norm"])
        else:
            base = str(row["title"])

        norm = normalize_title_for_lookup(base)
        cat = str(row["main_category_manual"]).strip()

        if not norm or not cat:
            continue

        # Nếu key đã tồn tại thì bỏ qua các dòng sau (KHÔNG lấy trùng title_norm)
        if norm in mapping:
            dup_skipped += 1
            continue

        mapping[norm] = cat
        usable_rows += 1

    print(
        f"Tổng số dòng manual dùng được (có cat & key sau khi chuẩn hóa): {usable_rows}")
    if dup_skipped > 0:
        print(
            f"- Đã bỏ qua {dup_skipped} dòng trùng title/title_norm (giữ mapping ở dòng xuất hiện đầu tiên).")

    print("Tổng số key mapping:", len(mapping))
    return mapping


# =========================
# CHẠY SCRIPT
# =========================

def main():
    # 1) Đọc mapping
    title_to_cat = load_manual_mapping(MANUAL_CSV)

    # 2) Đọc file sách
    print("Đọc file Excel:", INPUT_EXCEL)

    # Nếu muốn chắc chắn cover_url luôn là string:
    try:
        df = pd.read_excel(INPUT_EXCEL, dtype={COVER_URL_COL: str})
    except ValueError:
        # Trường hợp file không có cột cover_url vẫn chạy bình thường
        df = pd.read_excel(INPUT_EXCEL)

    # Đảm bảo nếu có cột cover_url thì giữ nguyên dạng text, không biến thành số
    if COVER_URL_COL in df.columns:
        # Không ép 'nan' thành chuỗi, chỉ convert những giá trị không null
        df[COVER_URL_COL] = df[COVER_URL_COL].astype(str).where(
            df[COVER_URL_COL].notna(), None
        )

    if TITLE_COL not in df.columns:
        raise ValueError(
            f"Không tìm thấy cột '{TITLE_COL}' trong file {INPUT_EXCEL}. "
            f"Các cột hiện có: {', '.join(df.columns)}"
        )

    # 3) Chuẩn hóa title -> title_norm_from_code
    print("Đang chuẩn hóa tiêu đề để lookup...")
    df["title_norm_from_code"] = df[TITLE_COL].apply(
        normalize_title_for_lookup)

    # 4) Ánh xạ sang main_category_manual
    print("Đang map category từ file manual...")
    df["main_category_from_manual"] = df["title_norm_from_code"].map(
        title_to_cat)

    total = len(df)
    matched_mask = df["main_category_from_manual"].notna()
    matched = matched_mask.sum()
    unmatched = total - matched

    print(f"- Tổng số sách ban đầu: {total}")
    print(f"- Khớp được manual: {matched} ({matched/total:.1%})")

    # BỎ các sách không khớp manual ra khỏi kết quả cuối
    if unmatched > 0:
        print(
            f"- Sẽ LOẠI BỎ {unmatched} sách không có mapping manual khỏi file output.")
        df = df[matched_mask].copy()

    # 4b) Thống kê thêm: bao nhiêu key trong manual không được dùng
    used_keys = set(df["title_norm_from_code"])
    unused_keys = set(title_to_cat.keys()) - used_keys
    print(f"- Số key trong manual KHÔNG dùng tới: {len(unused_keys)}")

    # 5) Nếu có cột main_category_suggested thì tạo cột final:
    if "main_category_suggested" in df.columns:
        print("Phát hiện cột main_category_suggested, tạo cột main_category_final...")
        df["main_category_final"] = df["main_category_from_manual"]
        mask_no_manual = df["main_category_final"].isna()
        df.loc[mask_no_manual, "main_category_final"] = df.loc[mask_no_manual,
                                                               "main_category_suggested"]
    else:
        print("Không có cột main_category_suggested, chỉ dùng main_category_from_manual.")

    # 6) Ghi ra Excel
    print("Ghi ra:", OUTPUT_EXCEL)
    df.to_excel(OUTPUT_EXCEL, index=False)
    print("Xong! Mở file", OUTPUT_EXCEL, "để kiểm tra.")


if __name__ == "__main__":
    main()
