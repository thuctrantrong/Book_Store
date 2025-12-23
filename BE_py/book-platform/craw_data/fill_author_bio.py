import mysql.connector
from mysql.connector import Error
import random

# ================== CẤU HÌNH KẾT NỐI MYSQL ==================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1900561275Nghia@",
    "database": "bookstore",
    "port": 3306,
}

# ================== HÀM TẠO BIO GIẢ ==================


def generate_bio(author_name, categories_str):
    """
    Tạo đoạn bio ngắn tiếng Việt cho 1 tác giả,
    dùng tên + danh sách thể loại nếu có.
    """
    name = author_name.strip()
    last_name = name.split()[-1] if name else ""

    categories = []
    if categories_str:
        categories = [c.strip()
                      for c in categories_str.split(",") if c.strip()]

    main_cat = categories[0] if categories else None

    templates_with_cat = [
        "{name} là tác giả có nhiều tác phẩm được xuất bản tại Việt Nam, "
        "tập trung vào chủ đề {cat}. Sách của {short} thường được độc giả đánh giá cao "
        "nhờ nội dung gần gũi và văn phong dễ tiếp cận.",

        "{name} là tác giả chuyên viết về mảng {cat}. "
        "Các tác phẩm của {short} kết hợp giữa kiến thức thực tiễn và cách trình bày sinh động, "
        "phù hợp với nhiều đối tượng độc giả.",

        "{name} được biết đến qua nhiều đầu sách thuộc thể loại {cat}. "
        "Phong cách viết của {short} chú trọng tính rõ ràng, logic và dễ áp dụng vào cuộc sống."
    ]

    templates_generic = [
        "{name} là tác giả có nhiều tác phẩm được xuất bản trên thị trường sách Việt Nam. "
        "Sách của {short} thường mang đến góc nhìn dễ hiểu, phù hợp với bạn đọc phổ thông.",

        "{name} tham gia thị trường xuất bản với nhiều đầu sách ở nhiều chủ đề khác nhau. "
        "Các tác phẩm của {short} hướng đến việc giúp người đọc tiếp cận kiến thức một cách đơn giản và trực quan.",

        "{name} là một trong những tác giả có sách được phân phối rộng rãi trong các nhà sách và nền tảng trực tuyến. "
        "Nội dung sách của {short} thường được biên soạn mạch lạc, gần gũi với thực tế."
    ]

    if main_cat:
        tpl = random.choice(templates_with_cat)
        bio = tpl.format(name=name, short=last_name or name, cat=main_cat)
    else:
        tpl = random.choice(templates_generic)
        bio = tpl.format(name=name, short=last_name or name)

    return bio


def main():
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

    # Lấy danh sách tác giả thiếu bio + các thể loại gắn với tác giả đó
    # (dùng GROUP_CONCAT để gom thể loại)
    query = """
        SELECT 
            a.author_id,
            a.author_name,
            GROUP_CONCAT(DISTINCT c.category_name ORDER BY c.category_name SEPARATOR ', ') AS categories
        FROM authors a
        LEFT JOIN books b ON b.author_id = a.author_id
        LEFT JOIN book_categories bc ON bc.book_id = b.book_id
        LEFT JOIN categories c ON c.category_id = bc.category_id
        WHERE a.bio IS NULL OR a.bio = ''
        GROUP BY a.author_id, a.author_name
    """
    cursor.execute(query)
    authors = cursor.fetchall()

    if not authors:
        print("Không có tác giả nào thiếu bio.")
        cursor.close()
        conn.close()
        return

    print(f"Tìm thấy {len(authors)} tác giả thiếu bio. Bắt đầu cập nhật...")

    updated = 0
    for idx, a in enumerate(authors, start=1):
        author_id = a["author_id"]
        author_name = a["author_name"] or ""
        categories_str = a["categories"] or ""

        bio = generate_bio(author_name, categories_str)

        cursor.execute(
            "UPDATE authors SET bio = %s WHERE author_id = %s",
            (bio, author_id)
        )
        updated += 1

        if updated % 50 == 0:
            conn.commit()
            print(f"Đã cập nhật {updated}/{len(authors)} tác giả...")

    conn.commit()
    print(f"Hoàn thành. Đã cập nhật bio cho {updated} tác giả.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
