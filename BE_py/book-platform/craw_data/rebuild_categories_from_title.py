import pandas as pd
import unicodedata
import re

# =========================
# CẤU HÌNH CƠ BẢN
# =========================

INPUT_EXCEL = "merged_books.xlsx"
OUTPUT_EXCEL = "merged_books_with_manual_category.xlsx"
MANUAL_CSV = "./fixbug_category_name/manual_title_categories.csv"  # file bạn đã tạo

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
