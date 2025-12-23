import os
from pathlib import Path
from typing import List
import unicodedata
import re

import pandas as pd


# ================== CẤU HÌNH CƠ BẢN ==================

BASE_DIR = Path(__file__).resolve().parent

GOOGLE_FILE = BASE_DIR / "google_api_scraper" / \
    "googlebooks_vi_multi_enriched.xlsx"
EBOOKVIE_FILE = BASE_DIR / "ebookvie" / "ebookvie_books.xlsx"
OUTPUT_FILE = BASE_DIR / "merged_books.xlsx"

STANDARD_COLUMNS: List[str] = [
    "title",
    "author_name",
    "categories",
    "description",
    "published_date",
    "language",
    "publisher",
    "page_count",
    "isbn_10",
    "isbn_13",
    "cover_url",
    "info_link",
    "source_url",
    "source",
]


# ================== HÀM TIỆN ÍCH ==================

def ensure_columns(df: pd.DataFrame, required_cols: List[str]) -> pd.DataFrame:
    """
    Đảm bảo DataFrame có đủ các cột trong required_cols.
    Nếu thiếu cột nào thì thêm cột đó với giá trị None.
    """
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    return df


def normalize_text_columns(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """
    Chuẩn hoá các cột text: fillna(''), ép string, strip khoảng trắng.
    """
    for col in cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
    return df


def normalize_for_dedup(text: str) -> str:
    """
    Chuẩn hoá chuỗi để so sánh trùng:
    - lower()
    - bỏ dấu tiếng Việt
    - chỉ giữ a-z, 0-9, khoảng trắng
    - gom nhiều space về 1 space
    """
    if not isinstance(text, str):
        text = "" if pd.isna(text) else str(text)

    text = text.strip().lower()
    if not text:
        return ""

    # Bỏ dấu: NFD rồi loại các ký tự Mn (mark nonspacing)
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")

    # Chỉ giữ a-z, 0-9, space
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ================== HÀM CHÍNH ==================

def merge_books(
    google_file: Path = GOOGLE_FILE,
    ebookvie_file: Path = EBOOKVIE_FILE,
    output_file: Path = OUTPUT_FILE,
) -> None:
    # ====== 1. KIỂM TRA FILE ======
    if not google_file.exists():
        print(f"❌ Không tìm thấy file: {google_file}")
        return
    if not ebookvie_file.exists():
        print(f"❌ Không tìm thấy file: {ebookvie_file}")
        return

    # ====== 2. ĐỌC EXCEL ======
    print(f"Đang đọc dữ liệu từ Google Books: {google_file}")
    df_google = pd.read_excel(google_file)

    print(f"Đang đọc dữ liệu từ ebookvie: {ebookvie_file}")
    df_ebookvie = pd.read_excel(ebookvie_file)

    # ====== 3. CHUẨN HOÁ GOOGLE BOOKS ======
    df_google = ensure_columns(df_google, STANDARD_COLUMNS)

    # Nếu Google chưa có source_url thì map từ info_link
    if "source_url" not in df_google.columns or df_google["source_url"].isna().all():
        df_google["source_url"] = df_google["info_link"]

    df_google["source"] = "google_books"

    # ====== 4. CHUẨN HOÁ EBOOKVIE ======
    if "cover_url" not in df_ebookvie.columns:
        if "image_url" in df_ebookvie.columns:
            df_ebookvie["cover_url"] = df_ebookvie["image_url"]
        else:
            df_ebookvie["cover_url"] = None

    if "language" not in df_ebookvie.columns:
        df_ebookvie["language"] = "vi"

    df_ebookvie = ensure_columns(df_ebookvie, STANDARD_COLUMNS)
    df_ebookvie["source"] = "ebookvie"

    # ====== 5. GỘP 2 DATAFRAME ======
    df_all = pd.concat([df_google, df_ebookvie], ignore_index=True)

    # Chuẩn hoá text cho một số cột quan trọng
    df_all = normalize_text_columns(
        df_all, ["title", "author_name", "isbn_10", "isbn_13"]
    )

    # Thêm cột normalized cho title & author để dùng trong dedup không dấu
    df_all["norm_title"] = df_all["title"].apply(normalize_for_dedup)
    df_all["norm_author_name"] = df_all["author_name"].apply(
        normalize_for_dedup)

    print("Tổng số bản ghi trước khi loại trùng:", len(df_all))

    # ====== 6. LOẠI TRÙNG ======
    # Chia 2 nhóm: có isbn_13 và không
    df_has_isbn = df_all[df_all["isbn_13"] != ""].copy()
    df_no_isbn = df_all[df_all["isbn_13"] == ""].copy()

    # Nhóm có ISBN_13: dedup theo isbn_13
    before_has = len(df_has_isbn)
    df_has_isbn = df_has_isbn.drop_duplicates(subset=["isbn_13"])
    after_has = len(df_has_isbn)
    print(f"Loại trùng nhóm có ISBN_13: {before_has} -> {after_has}")

    # Nhóm không có ISBN_13:
    # 👉 dedup theo norm_title + norm_author_name (không dấu, lowercase)
    before_no = len(df_no_isbn)
    df_no_isbn = df_no_isbn.drop_duplicates(
        subset=["norm_title", "norm_author_name"]
    )
    after_no = len(df_no_isbn)
    print(
        f"Loại trùng nhóm không có ISBN_13 (title + author, đã bỏ dấu): "
        f"{before_no} -> {after_no}"
    )

    # Gộp lại
    df_merged = pd.concat([df_has_isbn, df_no_isbn], ignore_index=True)
    print("Tổng số bản ghi sau khi loại trùng:", len(df_merged))

    # Bỏ các cột norm dùng nội bộ
    df_merged.drop(columns=["norm_title", "norm_author_name"],
                   inplace=True, errors="ignore")

    # Đảm bảo đúng thứ tự cột & sort cho dễ nhìn
    df_merged = ensure_columns(df_merged, STANDARD_COLUMNS)
    df_merged = df_merged[STANDARD_COLUMNS]

    df_merged = df_merged.sort_values(
        by=["title", "author_name"], ascending=True)

    # ====== 7. LƯU FILE KẾT QUẢ ======
    df_merged.to_excel(output_file, index=False)
    print(f"✅ Đã lưu file gộp: {output_file}")


def main():
    merge_books()


if __name__ == "__main__":
    main()
