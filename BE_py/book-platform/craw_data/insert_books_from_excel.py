import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

import mysql.connector
from mysql.connector import Error
import pandas as pd

from dotenv import load_dotenv
import math
import pandas as pd  # bạn đã import rồi, giữ nguyên

import random


def generate_book_price(main_cat: str | None) -> float:
    """
    Sinh giá sách (VNĐ) theo category chính.
    Giá trả về là số float, nhưng luôn là bội số của 1.000.
    """
    if not main_cat:
        main_cat = ""
    cat = main_cat.lower()

    # Thiếu nhi / truyện tranh
    if "thiếu nhi" in cat or "truyện tranh" in cat or "manga" in cat or "comic" in cat:
        price = random.randint(30, 80) * 1000        # 30k - 80k

    # Kinh tế, tài chính, marketing, quản trị
    elif "kinh tế" in cat or "tài chính" in cat or "marketing" in cat \
         or "quản trị" in cat or "khởi nghiệp" in cat:
        price = random.randint(80, 200) * 1000       # 80k - 200k

    # Kỹ năng sống, phát triển bản thân, tâm lý
    elif "kỹ năng" in cat or "kĩ năng" in cat or "phát triển bản thân" in cat \
         or "tâm lý" in cat or "tâm lý" in cat:
        price = random.randint(70, 180) * 1000       # 70k - 180k

    # Công nghệ thông tin, lập trình, khoa học
    elif "công nghệ" in cat or "lập trình" in cat or "khoa học" in cat \
         or "cntt" in cat:
        price = random.randint(100, 250) * 1000      # 100k - 250k

    # Văn học, tiểu thuyết, truyện ngắn
    elif "văn học" in cat or "tiểu thuyết" in cat or "truyện ngắn" in cat \
         or "ngôn tình" in cat or "thơ" in cat:
        price = random.randint(60, 150) * 1000       # 60k - 150k

    # Lịch sử, văn hóa, tôn giáo
    elif "lịch sử" in cat or "văn hóa" in cat or "tôn giáo" in cat:
        price = random.randint(80, 220) * 1000       # 80k - 220k

    # Giáo trình, sách giáo khoa, tham khảo
    elif "giáo khoa" in cat or "tham khảo" in cat or "giáo trình" in cat:
        price = random.randint(70, 200) * 1000       # 70k - 200k

    # Fallback chung
    else:
        price = random.randint(50, 180) * 1000       # 50k - 180k

    return float(price)


def none_if_nan(value):
    """
    Nếu value là NaN / pandas.NA / None / chuỗi rỗng -> trả về None.
    Ngược lại trả về chính nó.
    """
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    # Nếu là chuỗi 'nan', 'NaN', 'null', 'None'... thì cũng coi như None
    s = str(value).strip()
    if s.lower() in ("nan", "none", "null", "na", "n/a"):
        return None
    return value


# ================== CẤU HÌNH CƠ BẢN ==================

BASE_DIR = Path(__file__).resolve().parent
EXCEL_FILE = BASE_DIR / "merged_books_with_manual_category.xlsx"

# Đọc .env nếu có
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DB", "bookstore"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
}


# ================== HÀM TIỆN ÍCH ==================

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print("✅ Kết nối MySQL thành công.")
            return conn
    except Error as e:
        print("❌ Lỗi kết nối MySQL:", e)
    return None


def parse_year(published_date: Any) -> Optional[int]:
    """
    Lấy năm (4 chữ số đầu tiên) từ trường published_date (vd: '2017-05-01', '2019', '2018-?').
    Không parse được -> None.
    """
    if published_date is None:
        return None
    s = str(published_date).strip()
    if not s:
        return None
    m = re.search(r"(\d{4})", s)
    if not m:
        return None
    try:
        year = int(m.group(1))
        if 1000 <= year <= 2100:
            return year
    except ValueError:
        return None
    return None


def normalize_isbn_value(raw: Any) -> str:
    """
    Chuẩn hóa 1 giá trị ISBN từ Excel:
    - NaN, None, 'nan', 'NaN', 'null', 'None', 'N/A' -> ''
    - Cắt về tối đa 13 ký tự
    """
    s = str(raw).strip()
    if not s:
        return ""
    s_lower = s.lower()
    if s_lower in ("nan", "none", "null", "na", "n/a"):
        return ""
    # Cắt về tối đa 13 ký tự
    return s[:13]


def choose_isbn(row: pd.Series) -> Optional[str]:
    """
    Chọn isbn để insert:
    - ưu tiên isbn_13
    - nếu không có -> dùng isbn_10
    - nếu đều trống -> None
    """
    isbn_13 = normalize_isbn_value(row.get("isbn_13", ""))
    isbn_10 = normalize_isbn_value(row.get("isbn_10", ""))

    if isbn_13:
        return isbn_13
    if isbn_10:
        return isbn_10
    return None


# ================== CÁC BƯỚC INSERT ==================

def clear_old_data(conn):
    """
    Xóa dữ liệu cũ trong các bảng liên quan trước khi insert.
    Giữ nguyên cấu trúc bảng.
    Thứ tự xóa phải tôn trọng foreign key.
    """
    cursor = conn.cursor()
    print("🔄 Đang xóa dữ liệu cũ...")

    # Tạm tắt FK để truncate cho dễ
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    tables = [
        "book_images",
        "book_categories",
        "books",
        "categories",
        "authors",
        "publishers",
        # Các bảng khác nếu bạn muốn xóa sạch luôn (tùy):
        # "ratings", "user_actions", "recommendations", ...
    ]

    for tbl in tables:
        print(f"  TRUNCATE TABLE {tbl}...")
        cursor.execute(f"TRUNCATE TABLE {tbl}")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    cursor.close()
    print("✅ Đã xóa dữ liệu cũ trong các bảng liên quan.")


def load_excel() -> pd.DataFrame:
    if not EXCEL_FILE.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {EXCEL_FILE}")
    print(f"📖 Đang đọc file Excel: {EXCEL_FILE}")
    df = pd.read_excel(EXCEL_FILE)

    # Chuẩn hóa các cột chính
    for col in ["title", "author_name", "publisher", "language", "cover_url"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str).str.strip()

    # Cột category chính từ manual
    if "main_category_from_manual" not in df.columns:
        raise ValueError(
            "File Excel không có cột 'main_category_from_manual'. "
            "Hãy kiểm tra lại bước rebuild_categories_from_title."
        )

    df["main_category_from_manual"] = (
        df["main_category_from_manual"].fillna("").astype(str).str.strip()
    )

    # Loại bỏ các dòng không có title hoặc không có category
    before = len(df)
    df = df[(df["title"] != "") & (df["main_category_from_manual"] != "")]
    after = len(df)
    print(
        f"📦 Số sách dùng được sau khi lọc title & category: {after} (bỏ {before - after})")

    return df


def insert_authors(conn, df: pd.DataFrame) -> Dict[str, int]:
    """
    Insert unique authors vào bảng authors.
    Trả về mapping author_name -> author_id.
    """
    cursor = conn.cursor()
    author_names = sorted(set(df["author_name"].tolist()))
    author_names = [a for a in author_names if a]  # bỏ rỗng

    print(f"🧑‍💻 Số tác giả unique: {len(author_names)}")

    sql = "INSERT IGNORE INTO authors (author_name, bio, status) VALUES (%s, %s, %s)"
    data = [(name, None, "active") for name in author_names]
    if data:
        cursor.executemany(sql, data)
        conn.commit()
        print(f"✅ Đã insert {cursor.rowcount} tác giả.")

    # Lấy mapping lại
    cursor.execute("SELECT author_id, author_name FROM authors")
    rows = cursor.fetchall()
    author_map = {name: aid for (aid, name) in rows}
    cursor.close()
    return author_map


def insert_publishers(conn, df: pd.DataFrame) -> Dict[str, int]:
    """
    Insert unique publishers vào bảng publishers.
    Trả về mapping publisher_name -> publisher_id.
    """
    cursor = conn.cursor()
    publisher_names = sorted(set(df["publisher"].tolist()))
    publisher_names = [p for p in publisher_names if p]

    print(f"🏢 Số NXB unique: {len(publisher_names)}")

    sql = "INSERT IGNORE INTO publishers (publisher_name, status) VALUES (%s, %s)"

    data = [(name, "active") for name in publisher_names]
    if data:
        cursor.executemany(sql, data)
        conn.commit()
        print(f"✅ Đã insert {cursor.rowcount} NXB.")

    cursor.execute("SELECT publisher_id, publisher_name FROM publishers")
    rows = cursor.fetchall()
    publisher_map = {name: pid for (pid, name) in rows}
    cursor.close()
    return publisher_map


def insert_categories(conn, df: pd.DataFrame) -> Dict[str, int]:
    """
    Insert unique categories (từ main_category_from_manual) vào bảng categories.
    Trả về mapping category_name -> category_id.
    """
    cursor = conn.cursor()
    cat_names = sorted(set(df["main_category_from_manual"].tolist()))
    cat_names = [c for c in cat_names if c]

    print(f"🏷️  Số category unique: {len(cat_names)}")

    sql = "INSERT IGNORE INTO categories (category_name, status) VALUES (%s, %s)"

    data = [(name, "active") for name in cat_names]
    if data:
        cursor.executemany(sql, data)
        conn.commit()
        print(f"✅ Đã insert {cursor.rowcount} category.")

    cursor.execute("SELECT category_id, category_name FROM categories")
    rows = cursor.fetchall()
    category_map = {name: cid for (cid, name) in rows}
    cursor.close()
    return category_map


def insert_books_and_children(
    conn,
    df: pd.DataFrame,
    author_map: Dict[str, int],
    publisher_map: Dict[str, int],
    category_map: Dict[str, int],
):
    """
    Insert books, book_categories, book_images.
    Đảm bảo mỗi dòng sách trong df tạo ra:
      - 1 row trong books
      - 1 row trong book_categories
      - 1 row trong book_images
    => Tổng số dòng 3 bảng này như nhau.
    """
    cursor = conn.cursor()

    book_sql = """
        INSERT INTO books
        (title, author_id, publisher_id, price, stock_quantity,
         description, publication_year, isbn, avg_rating, rating_count,
         language, format, status)
        VALUES
        (%s, %s, %s, %s, %s,
         %s, %s, %s, %s, %s,
         %s, %s, %s)
    """

    book_category_sql = """
        INSERT INTO book_categories (book_id, category_id)
        VALUES (%s, %s)
    """

    book_image_sql = """
        INSERT INTO book_images (book_id, image_url, is_main)
        VALUES (%s, %s, %s)
    """

    book_count = 0
    used_isbn = set()  # thêm dòng này trước vòng for

    for idx, row in df.iterrows():
        title = str(row.get("title", "")).strip()
        if not title:
            continue

        author_name = str(row.get("author_name", "")).strip()
        publisher_name = str(row.get("publisher", "")).strip()

        # description có thể là NaN -> convert
        description_raw = row.get("description", None)
        description = none_if_nan(description_raw)

        # published_date có thể NaN -> convert trước khi parse_year
        published_date_raw = none_if_nan(row.get("published_date", None))
        pub_year = parse_year(published_date_raw)

        language_raw = row.get("language", "")
        language = none_if_nan(language_raw)
        if language is not None:
            language = str(language).strip() or None

        isbn = choose_isbn(row)

        # Tránh trùng ISBN trong cùng batch
        if isbn:
            if isbn in used_isbn:
                # Nếu ISBN đã dùng rồi, bỏ ISBN cho bản ghi này (insert NULL)
                # print(f"⚠️ ISBN trùng trong batch, bỏ ISBN cho sách: {title} ({isbn})")
                isbn = None
            else:
                used_isbn.add(isbn)

        # Giá & tồn kho: bạn tùy chỉnh
        main_cat = row.get("main_category_from_manual")
        price = generate_book_price(main_cat)
        stock_quantity = random.randint(100, 1000)

        avg_rating = 0.0
        rating_count = 0

        book_format = "paperback"
        status = "active"

        author_id = author_map.get(author_name)
        publisher_id = publisher_map.get(publisher_name)

        book_values = (
            title,
            author_id,
            publisher_id,
            price,
            stock_quantity,
            description,   # đã none_if_nan
            pub_year,      # int hoặc None
            isbn,          # string hoặc None
            avg_rating,
            rating_count,
            language,      # string hoặc None
            book_format,
            status,
        )
        cursor.execute(book_sql, book_values)

        book_id = cursor.lastrowid

        # book_categories
        cat_name = str(row.get("main_category_from_manual", "")).strip()
        category_id = category_map.get(cat_name)
        if category_id:
            cursor.execute(book_category_sql, (book_id, category_id))
        else:
            print(
                f"⚠️  Không tìm thấy category_id cho '{cat_name}' (book: {title})")

        # book_images
        cover_url_raw = row.get("cover_url", "")
        cover_url = none_if_nan(cover_url_raw)
        if cover_url:
            cover_url = str(cover_url).strip()
            cursor.execute(book_image_sql, (book_id, cover_url, 1))
        else:
            print(f"⚠️  Sách '{title}' không có cover_url.")

    conn.commit()
    cursor.close()
    print(f"✅ Đã insert {book_count} sách + categories + images.")


def main():
    conn = get_connection()
    if not conn:
        return

    try:
        # 1) Xóa dữ liệu cũ
        clear_old_data(conn)

        # 2) Đọc file Excel
        df = load_excel()

        # 3) Insert authors, publishers, categories
        author_map = insert_authors(conn, df)
        publisher_map = insert_publishers(conn, df)
        category_map = insert_categories(conn, df)

        # 4) Insert books + book_categories + book_images
        insert_books_and_children(
            conn, df, author_map, publisher_map, category_map)

        print("🎉 Hoàn tất import dữ liệu sách vào database 'bookstore'.")

    finally:
        conn.close()
        print("🔌 Đã đóng kết nối MySQL.")


if __name__ == "__main__":
    main()
