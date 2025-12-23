import pandas as pd
import mysql.connector
from mysql.connector import Error
import re

# ================ CẤU HÌNH ================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1900561275Nghia@",
    "database": "bookstore",
    "port": 3306,
}

EXCEL_FILE = "merged_books_with_main_category.xlsx"


# ================ HÀM HỖ TRỢ ================

def normalize_str(s):
    if s is None:
        return ""
    return str(s).strip()


def clean_isbn_field(raw):
    """
    Làm sạch một trường ISBN (có thể là NaN, chứa nhiều mã, ký tự lạ,...)
    - Trả về chuỗi ISBN 10 hoặc 13 ký tự (chỉ chứa 0-9 và X)
    - Nếu không tìm được ISBN hợp lệ -> trả về None
    """
    s = normalize_str(raw)
    if not s:
        return None

    if s.lower() in ("nan", "none", "null", "na", "n/a"):
        return None

    candidates = re.split(r"[ ,;/]+", s)
    for cand in candidates:
        cand = cand.strip()
        if not cand:
            continue

        cand_clean = re.sub(r"[^0-9Xx]", "", cand)
        if len(cand_clean) == 10 or len(cand_clean) == 13:
            return cand_clean.upper()

    return None


def choose_isbn(row):
    """
    Ưu tiên isbn_13 (sau khi clean), nếu không có thì dùng isbn_10 (clean).
    Nếu vẫn không có ISBN hợp lệ -> None.
    """
    isbn = clean_isbn_field(row.get("isbn_13"))
    if not isbn:
        isbn = clean_isbn_field(row.get("isbn_10"))
    return isbn


def normalize_main_cat(val):
    """
    Chuẩn hóa main_category_suggested:
    - Rỗng / NaN / None -> 'Khác'
    - 'khac', 'khác' (hoa/thường) -> 'Khác'
    - Còn lại giữ nguyên (đã strip)
    """
    s = normalize_str(val)
    if not s:
        return "Khác"

    low = s.lower()
    if low in ("nan", "none", "null", "na", "n/a"):
        return "Khác"

    if low in ("khac", "khác"):
        return "Khác"

    return s


# ================ MAIN ================

def main():
    print(f"Đang đọc file: {EXCEL_FILE}")
    df = pd.read_excel(EXCEL_FILE)

    if df.empty:
        print("File Excel rỗng, không có dữ liệu.")
        return

    # Đảm bảo các cột tối thiểu
    for col in ["title", "isbn_10", "isbn_13", "main_category_suggested"]:
        if col not in df.columns:
            df[col] = None

    if "main_category_suggested" not in df.columns:
        print("File Excel KHÔNG có cột 'main_category_suggested' – không thể build categories.")
        return

    # Kết nối MySQL
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if not conn.is_connected():
            print("Kết nối MySQL thất bại.")
            return
        cursor = conn.cursor(dictionary=True)
        print("Kết nối MySQL thành công.")
    except Error as e:
        print("Lỗi kết nối MySQL:", e)
        return

    # ========== TRUNCATE categories & book_categories ==========
    print("TRUNCATE categories và book_categories ...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE book_categories")
    cursor.execute("TRUNCATE TABLE categories")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()

    # ========== BUILD categories từ main_category_suggested (DISTINCT) ==========
    print("Đang gom các main_category_suggested distinct để tạo bảng categories...")

    distinct_main_cats = set()
    for _, row in df.iterrows():
        mc = normalize_main_cat(row.get("main_category_suggested"))
        distinct_main_cats.add(mc)

    distinct_main_cats = sorted(distinct_main_cats)

    if not distinct_main_cats:
        print("Không có main_category_suggested hợp lệ trong Excel.")
        cursor.close()
        conn.close()
        return

    category_name_to_id = {}
    print(
        f"Số category sẽ insert vào bảng categories: {len(distinct_main_cats)}")

    for name in distinct_main_cats:
        cursor.execute(
            "INSERT INTO categories (category_name, status) VALUES (%s, %s)",
            (name, "active"),
        )
        cid = cursor.lastrowid
        category_name_to_id[name] = cid

    conn.commit()
    print("Đã tạo xong bảng categories từ main_category_suggested.")

    # ========== BUILD CACHE books (isbn/title -> book_id) ==========
    print("Đang load toàn bộ sách từ bảng books để tạo cache...")

    cursor.execute("SELECT book_id, isbn, title FROM books")
    books = cursor.fetchall()

    book_cache_isbn = {}
    book_cache_title = {}

    for b in books:
        bid = b["book_id"]
        isbn = normalize_str(b.get("isbn"))
        title = normalize_str(b.get("title"))

        if isbn:
            book_cache_isbn[isbn] = bid
        if title and title not in book_cache_title:
            book_cache_title[title] = bid

    print(
        f"Cache sách: {len(book_cache_isbn)} theo ISBN, {len(book_cache_title)} theo title.")

    def find_book_id(row):
        """
        Tìm book_id dựa trên isbn (ưu tiên) hoặc title.
        Không query DB nữa, chỉ dùng cache đã load.
        """
        isbn = choose_isbn(row)
        title = normalize_str(row.get("title"))

        if isbn and isbn in book_cache_isbn:
            return book_cache_isbn[isbn]

        if title and title in book_cache_title:
            return book_cache_title[title]

        return None

    # ========== GÁN book -> main_category_suggested ==========
    total_rows = len(df)
    linked_count = 0
    skipped_no_book = 0

    print("Bắt đầu gắn book -> main_category_suggested ...")

    batch_values = []
    BATCH_SIZE = 500

    for idx, row in df.iterrows():
        book_id = find_book_id(row)
        if not book_id:
            skipped_no_book += 1
            continue

        main_cat = normalize_main_cat(row.get("main_category_suggested"))

        cid = category_name_to_id.get(main_cat)
        if not cid:
            continue

        batch_values.append((book_id, cid))
        linked_count += 1

        if len(batch_values) >= BATCH_SIZE:
            cursor.executemany(
                """
                INSERT IGNORE INTO book_categories (book_id, category_id)
                VALUES (%s, %s)
                """,
                batch_values,
            )
            conn.commit()
            batch_values.clear()
            print(
                f"Đã gắn category cho {linked_count}/{total_rows} dòng Excel...")

    # Flush batch cuối
    if batch_values:
        cursor.executemany(
            """
            INSERT IGNORE INTO book_categories (book_id, category_id)
            VALUES (%s, %s)
            """,
            batch_values,
        )
        conn.commit()

    print("Gắn category theo Excel xong.")
    print(f"Đã gắn category cho {linked_count} dòng Excel.")
    print(
        f"Sách trong Excel nhưng không tìm thấy trong 'books': {skipped_no_book}")

    # ========== BƯỚC CUỐI: GẮN 'Khác' CHO MỌI SÁCH CÒN TRỐNG ==========
    print("Đang gắn category 'Khác' cho các sách chưa có category nào...")

    # Lấy category_id tương ứng 'Khác'
    id_khac = category_name_to_id.get("Khác")
    if id_khac:
        cursor.execute(
            """
            INSERT IGNORE INTO book_categories (book_id, category_id)
            SELECT b.book_id, %s
            FROM books b
            LEFT JOIN book_categories bc ON b.book_id = bc.book_id
            WHERE bc.book_id IS NULL
            """,
            (id_khac,),
        )
        conn.commit()

        # Đếm lại cho chắc
        cursor.execute(
            "SELECT COUNT(DISTINCT book_id) AS cnt FROM book_categories")
        row_cnt = cursor.fetchone()
        total_with_cat = row_cnt["cnt"] if row_cnt else 0
        print(f"Tổng số sách đã có ít nhất 1 category: {total_with_cat}")

    else:
        print("Không tìm thấy category 'Khác' trong bảng categories!")

    print("=======================================")
    print("Hoàn thành toàn bộ quá trình build categories + mapping.")
    print("=======================================")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
