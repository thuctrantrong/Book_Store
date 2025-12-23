import pandas as pd
from pathlib import Path

# ================== CẤU HÌNH ĐƯỜNG DẪN ==================

BASE_DIR = Path(__file__).resolve().parent

MERGED_FILE = BASE_DIR / "merged_books.xlsx"
MERGED_WITH_MANUAL_FILE = BASE_DIR / "merged_books_with_manual_category.xlsx"
OUTPUT_UNMAPPED_FILE = BASE_DIR / "merged_books_unmapped.xlsx"


def build_key(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tạo key dùng để so sánh 2 file:
    key = (title | author_name | published_date)
    Dùng bản gốc, không bỏ dấu – vì file with_manual là subset của merged_books.
    """
    for col in ["title", "author_name", "published_date"]:
        if col not in df.columns:
            df[col] = ""

    df["title"] = df["title"].fillna("").astype(str).str.strip()
    df["author_name"] = df["author_name"].fillna("").astype(str).str.strip()
    df["published_date"] = df["published_date"].fillna(
        "").astype(str).str.strip()

    df["_key"] = (
        df["title"] + " | " + df["author_name"] + " | " + df["published_date"]
    )
    return df


def main():
    # 1. Đọc file
    if not MERGED_FILE.exists():
        print(f"❌ Không tìm thấy file: {MERGED_FILE}")
        return
    if not MERGED_WITH_MANUAL_FILE.exists():
        print(f"❌ Không tìm thấy file: {MERGED_WITH_MANUAL_FILE}")
        return

    print(f"Đang đọc file gốc: {MERGED_FILE}")
    df_all = pd.read_excel(MERGED_FILE)

    print(f"Đang đọc file đã map manual: {MERGED_WITH_MANUAL_FILE}")
    df_mapped = pd.read_excel(MERGED_WITH_MANUAL_FILE)

    print(f"Tổng số sách trong merged_books.xlsx: {len(df_all)}")
    print(
        f"Số sách trong merged_books_with_manual_category.xlsx: {len(df_mapped)}")

    # 2. Tạo key cho cả hai DataFrame
    df_all = build_key(df_all)
    df_mapped = build_key(df_mapped)

    mapped_keys = set(df_mapped["_key"].tolist())
    print(f"Số key mapped: {len(mapped_keys)}")

    # 3. Lọc ra những bản ghi KHÔNG có trong mapped_keys
    df_unmapped = df_all[~df_all["_key"].isin(mapped_keys)].copy()
    df_unmapped.drop(columns=["_key"], inplace=True)

    print(f"Số sách KHÔNG có mapping manual (unmapped): {len(df_unmapped)}")

    # 4. Ghi ra file
    df_unmapped.to_excel(OUTPUT_UNMAPPED_FILE, index=False)
    print(f"✅ Đã lưu danh sách sách không mapping vào: {OUTPUT_UNMAPPED_FILE}")


if __name__ == "__main__":
    main()
