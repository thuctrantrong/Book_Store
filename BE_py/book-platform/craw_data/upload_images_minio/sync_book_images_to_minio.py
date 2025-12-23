import io
import os
from urllib.parse import urlparse

import requests
from minio import Minio
import mysql.connector
from mysql.connector import Error

# ============== CẤU HÌNH MYSQL ==============
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1900561275Nghia@",
    "database": "bookstore",
    "port": 3306,
}

# ============== CẤU HÌNH MINIO ==============
MINIO_ENDPOINT = "192.168.1.11:9000"
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "admin123456789"
MINIO_BUCKET = "bookstore"
MINIO_SECURE = False


def get_file_extension_from_url(url: str, default: str = ".jpg") -> str:
    """
    Lấy đuôi file từ URL. Nếu không có hoặc lạ -> trả về default (.jpg)
    """
    path = urlparse(url).path
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        return ext
    return default


def guess_content_type(ext: str) -> str:
    """
    Đoán content-type theo phần mở rộng.
    """
    ext = ext.lower()
    mapping = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return mapping.get(ext, "application/octet-stream")


def main():
    conn = None
    cursor = None
    try:
        # 1. Kết nối MySQL
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            if not conn.is_connected():
                print("❌ Kết nối MySQL thất bại.")
                return
            cursor = conn.cursor(dictionary=True)
            print("✅ Kết nối MySQL thành công.")
        except Error as e:
            print("❌ Lỗi kết nối MySQL:", e)
            return

        # 2. Kết nối MinIO
        minio_client = Minio(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
        )

        # 2.1. Tạo bucket nếu chưa tồn tại
        if not minio_client.bucket_exists(bucket_name=MINIO_BUCKET):
            print(f"🪣 Bucket '{MINIO_BUCKET}' chưa tồn tại. Đang tạo mới...")
            minio_client.make_bucket(bucket_name=MINIO_BUCKET)
            print(f"✅ Đã tạo bucket '{MINIO_BUCKET}'.")
        else:
            print(f"🪣 Bucket '{MINIO_BUCKET}' đã tồn tại.")

        # 3. Lấy danh sách ảnh cần migrate
        # Chỉ lấy link http(s) để migrate sang MinIO
        cursor.execute(
            """
            SELECT image_id, book_id, image_url
            FROM book_images
            WHERE image_url IS NOT NULL
              AND image_url <> ''
              AND (image_url LIKE 'http://%' OR image_url LIKE 'https://%')
            """
        )
        rows = cursor.fetchall()
        total = len(rows)
        print(f"📸 Tổng số ảnh cần migrate từ HTTP -> MinIO: {total}")

        migrated = 0
        failed = 0

        for idx, row in enumerate(rows, start=1):
            image_id = row["image_id"]
            book_id = row["book_id"]
            src_url = (row["image_url"] or "").strip()

            print(f"\n[{idx}/{total}] image_id={image_id}, book_id={book_id}")
            print(f"  Nguồn: {src_url}")

            # 4. Tải ảnh từ src_url
            try:
                resp = requests.get(src_url, timeout=20)
                resp.raise_for_status()
                content = resp.content
            except Exception as e:
                print("  ❌ Lỗi tải ảnh:", e)
                failed += 1
                continue

            if not content:
                print("  ❌ Ảnh rỗng, bỏ qua.")
                failed += 1
                continue

            # 5. Tạo object name cho MinIO
            ext = get_file_extension_from_url(src_url, default=".jpg")
            content_type = guess_content_type(ext)
            object_name = f"covers/books/{book_id}/{image_id}{ext}"

            # 6. Upload lên MinIO
            try:
                data_bytes = io.BytesIO(content)
                file_size = len(content)

                minio_client.put_object(
                    bucket_name=MINIO_BUCKET,
                    object_name=object_name,
                    data=data_bytes,
                    length=file_size,
                    content_type=content_type,
                )

                print(
                    f"  ✅ Đã upload lên MinIO: {MINIO_BUCKET}/{object_name}"
                )

                # 7. Cập nhật DB: lưu object_name (key) chứ không phải full URL
                cursor.execute(
                    "UPDATE book_images SET image_url = %s WHERE image_id = %s",
                    (object_name, image_id),
                )
                conn.commit()

                migrated += 1

            except Exception as e:
                print("  ❌ Lỗi upload MinIO hoặc update DB:", e)
                failed += 1
                conn.rollback()
                continue

        print("\n=========== TỔNG KẾT ===========")
        print(f"✅ Đã migrate: {migrated}")
        print(f"❌ Thất bại: {failed}")
        print(f"➡️  Tổng xử lý: {total}")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()
        print("🔌 Đã đóng kết nối MySQL.")


if __name__ == "__main__":
    main()
