import random
import string
import json
from datetime import datetime, timedelta

import mysql.connector
from mysql.connector import Error, IntegrityError

# ================== CẤU HÌNH KẾT NỐI MYSQL ==================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1900561275Nghia@",
    "database": "bookstore",
    "port": 3306,
}

# ================== THAM SỐ SINH DỮ LIỆU ==================
NUM_USERS = 300               # số user giả
MAX_ORDERS_PER_USER = 8       # tối đa đơn hàng mỗi user
MAX_WISHLIST_ITEMS_PER_USER = 10
MAX_CART_ITEMS_PER_USER = 5
RATING_PROB_PER_ORDER_ITEM = 0.4  # xác suất user đánh giá mỗi cuốn đã mua
EXTRA_VIEW_ACTIONS_PER_USER = 20  # số log view random thêm


# ================== HÀM HỖ TRỢ ==================

def rand_choice_weighted(options):
    """
    options: list các tuple (value, weight)
    trả về 1 value dựa trên weight.
    """
    total = sum(w for _, w in options)
    r = random.uniform(0, total)
    upto = 0
    for v, w in options:
        if upto + w >= r:
            return v
        upto += w
    return options[-1][0]


def random_name():
    first_names = [
        "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Võ", "Phan", "Đặng",
        "Bùi", "Đỗ", "Hồ", "Ngô"
    ]
    middle_names = ["Văn", "Thị", "Hồng", "Minh",
                    "Quang", "Thanh", "Thành", "Xuân"]
    last_names = [
        "Anh", "Bình", "Châu", "Dũng", "Hạnh", "Hải", "Hương", "Huy",
        "Lan", "Linh", "Long", "Nam", "Phong", "Thảo", "Trang"
    ]
    return f"{random.choice(first_names)} {random.choice(middle_names)} {random.choice(last_names)}"


def random_username(full_name, index):
    base = (
        full_name.lower()
        .replace(" ", "")
        .replace("đ", "d")
        .replace("ê", "e")
        .replace("â", "a")
        .replace("ă", "a")
        .replace("ơ", "o")
        .replace("ư", "u")
        .replace("ô", "o")
    )
    return f"{base}{index}"[:30]


def random_email(username):
    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]
    return f"{username}@{random.choice(domains)}"


def random_phone():
    prefix = random.choice(["09", "08", "03", "07", "05"])
    return prefix + "".join(random.choices(string.digits, k=8))


def random_password_hash():
    # Chỉ là chuỗi giả, không hash thật, đủ độ dài
    return "".join(random.choices(string.ascii_letters + string.digits, k=60))


def random_address_text():
    streets = ["Nguyễn Trãi", "Lê Lợi", "Hai Bà Trưng",
               "Điện Biên Phủ", "Trần Hưng Đạo", "Lý Thường Kiệt"]
    wards = ["P.1", "P.2", "P.3", "P.5", "P.7", "P.Bến Nghé", "P.Bến Thành"]
    districts = ["Q.1", "Q.3", "Q.5", "Q.7", "Q.Tân Bình", "Q.Bình Thạnh"]
    cities = ["TP.HCM", "Hà Nội", "Đà Nẵng", "Cần Thơ", "Hải Phòng"]
    return f"{random.randint(1, 999)} {random.choice(streets)}, {random.choice(wards)}, {random.choice(districts)}, {random.choice(cities)}"


def random_past_datetime(days=365):
    """
    Sinh 1 datetime ngẫu nhiên trong vòng 'days' ngày trở lại đây.
    """
    now = datetime.now()
    delta_days = random.randint(0, days)
    delta_seconds = random.randint(0, 24 * 3600)
    return now - timedelta(days=delta_days, seconds=delta_seconds)


def random_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def random_device():
    devices = [
        "Chrome on Windows",
        "Chrome on macOS",
        "Safari on iOS",
        "Chrome on Android",
        "Firefox on Linux",
    ]
    return random.choice(devices)


# ================== MAIN ==================

def main():
    random.seed(123)  # để chạy lại vẫn ra như cũ

    # 1. Kết nối DB
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

    # 2. Kiểm tra đã có sách chưa
    cursor.execute(
        "SELECT book_id, price FROM books WHERE status IN ('active','out_of_stock')")
    books = cursor.fetchall()
    if not books:
        print("Chưa có sách trong bảng books. Hãy import catalog trước.")
        return

    print(f"Có {len(books)} sách trong hệ thống. Bắt đầu sinh dữ liệu...")

    # ================== USERS & ADDRESSES ==================
    users = []
    print("Sinh users & addresses...")

    for i in range(1, NUM_USERS + 1):
        full_name = random_name()
        username = random_username(full_name, i)
        email = random_email(username)
        phone = random_phone()
        password_hash = random_password_hash()

        role = "customer"  # đa số là customer
        status = rand_choice_weighted([
            ("active", 0.85),
            ("unverified", 0.10),
            ("locked", 0.05),
        ])
        is_deleted = 0

        cursor.execute(
            """
            INSERT INTO users
                (username, email, password_hash, full_name, phone,
                 role, status, is_deleted)
            VALUES (%s, %s, %s, %s, %s,
                    %s, %s, %s)
            """,
            (username, email, password_hash, full_name, phone,
             role, status, is_deleted)
        )
        conn.commit()
        user_id = cursor.lastrowid
        users.append(user_id)

        # tạo 1–2 địa chỉ
        num_addr = random.randint(1, 2)
        default_index = random.randint(1, num_addr)
        for j in range(1, num_addr + 1):
            addr_text = random_address_text()
            is_default = 1 if j == default_index else 0
            cursor.execute(
                """
                INSERT INTO addresses (user_id, address_text, is_default)
                VALUES (%s, %s, %s)
                """,
                (user_id, addr_text, is_default)
            )
        conn.commit()

    print(f"Đã tạo {len(users)} users và địa chỉ tương ứng.")

    # Lấy lại addresses theo user để dùng cho orders
    cursor.execute("SELECT * FROM addresses")
    all_addresses = cursor.fetchall()
    addresses_by_user = {}
    for addr in all_addresses:
        addresses_by_user.setdefault(addr["user_id"], []).append(addr)

    # ================== PROMOTIONS ==================
    print("Sinh promotions...")
    promo_codes = []
    for i in range(1, 8):
        code = f"SALE{i:02d}"
        discount = random.choice([5, 10, 15, 20, 25, 30])
        start_date = datetime.now().date() - timedelta(days=random.randint(10, 100))
        end_date = start_date + timedelta(days=random.randint(10, 60))
        is_active = 1 if end_date >= datetime.now().date() else 0
        status = "active" if is_active else "inactive"

        cursor.execute(
            """
            INSERT INTO promotions
                (code, discount_percent, start_date, end_date,
                 is_active, status)
            VALUES (%s, %s, %s, %s,
                    %s, %s)
            """,
            (code, discount, start_date, end_date, is_active, status)
        )
        conn.commit()
        promo_id = cursor.lastrowid
        promo_codes.append({"promo_id": promo_id, "code": code})

    # ================== WISHLISTS & CARTS (cơ bản) ==================
    print("Sinh wishlists & carts cơ bản...")
    for user_id in users:
        # Wishlist (không phải user nào cũng có)
        if random.random() < 0.6:
            cursor.execute(
                "INSERT INTO wishlists (user_id) VALUES (%s)",
                (user_id,)
            )
            conn.commit()
            wishlist_id = cursor.lastrowid

            # chọn vài sách random
            num_items = random.randint(1, MAX_WISHLIST_ITEMS_PER_USER)
            sample_books = random.sample(books, min(num_items, len(books)))
            for b in sample_books:
                cursor.execute(
                    """
                    INSERT IGNORE INTO wishlist_items (wishlist_id, book_id)
                    VALUES (%s, %s)
                    """,
                    (wishlist_id, b["book_id"])
                )
            conn.commit()

        # Cart (một số user có giỏ chưa checkout)
        if random.random() < 0.5:
            cursor.execute(
                "INSERT INTO carts (user_id) VALUES (%s)",
                (user_id,)
            )
            conn.commit()
            cart_id = cursor.lastrowid

            num_items = random.randint(1, MAX_CART_ITEMS_PER_USER)
            sample_books = random.sample(books, min(num_items, len(books)))
            for b in sample_books:
                qty = random.randint(1, 3)
                cursor.execute(
                    """
                    INSERT INTO cart_items (cart_id, book_id, quantity)
                    VALUES (%s, %s, %s)
                    """,
                    (cart_id, b["book_id"], qty)
                )
            conn.commit()

    # ================== ORDERS, ORDER_DETAILS, PAYMENTS ==================
    print("Sinh orders, order_details, payments...")
    orders = []  # để dùng cho ratings & user_actions

    for user_id in users:
        num_orders = random.randint(0, MAX_ORDERS_PER_USER)
        user_addrs = addresses_by_user.get(user_id, [])
        if not user_addrs:
            continue

        for _ in range(num_orders):
            address = random.choice(user_addrs)
            address_id = address["address_id"]

            order_date = random_past_datetime(days=365)

            order_status = rand_choice_weighted([
                ("delivered", 0.6),
                ("processing", 0.1),
                ("pending", 0.05),
                ("shipped", 0.15),
                ("cancelled", 0.07),
                ("returned", 0.03),
                ("failed", 0.0),
            ])

            payment_method = rand_choice_weighted([
                ("COD", 0.5),
                ("CreditCard", 0.25),
                ("E-Wallet", 0.25),
            ])

            if order_status == "delivered":
                payment_status = "paid"
            elif order_status in ("cancelled", "failed"):
                payment_status = "unpaid"
            else:
                payment_status = rand_choice_weighted([
                    ("unpaid", 0.7),
                    ("paid", 0.3),
                ])

            promo_id = None
            if random.random() < 0.3 and promo_codes:
                promo = random.choice(promo_codes)
                promo_id = promo["promo_id"]

            cursor.execute(
                """
                INSERT INTO orders
                    (user_id, address_id, promo_id,
                     order_date, status, payment_method, payment_status)
                VALUES (%s, %s, %s,
                        %s, %s, %s, %s)
                """,
                (user_id, address_id, promo_id,
                 order_date, order_status, payment_method, payment_status)
            )
            conn.commit()
            order_id = cursor.lastrowid

            # ORDER_DETAILS
            num_items = random.randint(1, 5)
            order_books = random.sample(books, min(num_items, len(books)))
            order_total = 0.0
            for b in order_books:
                book_id = b["book_id"]
                unit_price = float(b["price"])
                quantity = random.randint(1, 3)
                total_price = unit_price * quantity
                order_total += total_price

                cursor.execute(
                    """
                    INSERT INTO order_details
                        (order_id, book_id, quantity, unit_price, total_price)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (order_id, book_id, quantity, unit_price, total_price)
                )

            conn.commit()

            # PAYMENTS
            if payment_status == "paid":
                provider = (
                    "COD" if payment_method == "COD"
                    else ("VNPAY" if payment_method == "E-Wallet" else "Visa/Master")
                )
                transaction_id = "".join(random.choices(
                    string.ascii_uppercase + string.digits, k=16))
                pay_status = "success"

                cursor.execute(
                    """
                    INSERT INTO payments
                        (order_id, amount, provider, transaction_id, status)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (order_id, order_total, provider, transaction_id, pay_status)
                )
                conn.commit()
            elif payment_status == "unpaid" and random.random() < 0.2:
                # một số đơn có payment failed
                provider = (
                    "COD" if payment_method == "COD"
                    else ("VNPAY" if payment_method == "E-Wallet" else "Visa/Master")
                )
                transaction_id = "".join(random.choices(
                    string.ascii_uppercase + string.digits, k=16))
                pay_status = "failed"
                cursor.execute(
                    """
                    INSERT INTO payments
                        (order_id, amount, provider, transaction_id, status)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (order_id, order_total, provider, transaction_id, pay_status)
                )
                conn.commit()

            orders.append({
                "order_id": order_id,
                "user_id": user_id,
                "order_date": order_date,
                "books": [b for b in order_books],
            })

    print(f"Đã tạo {len(orders)} orders.")

    # ================== RATINGS ==================
    print("Sinh ratings...")
    rating_count = 0
    for od in orders:
        user_id = od["user_id"]
        for b in od["books"]:
            if random.random() < RATING_PROB_PER_ORDER_ITEM:
                book_id = b["book_id"]
                rating_value = random.randint(
                    3, 5) if random.random() < 0.8 else random.randint(1, 5)
                review_text = None
                if random.random() < 0.4:
                    review_text = random.choice([
                        "Sách hay, nội dung dễ hiểu.",
                        "Rất đáng đọc, giao hàng nhanh.",
                        "Nội dung ổn nhưng trình bày hơi khó.",
                        "Chất lượng in tốt, sẽ ủng hộ tiếp.",
                    ])

                try:
                    cursor.execute(
                        """
                        INSERT INTO ratings
                            (user_id, book_id, rating, review, status)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (user_id, book_id, rating_value, review_text, "approved")
                    )
                    conn.commit()
                    rating_count += 1
                except IntegrityError:
                    # đã có rating user-book này
                    conn.rollback()
                    continue

    print(f"Đã tạo khoảng {rating_count} ratings.")

    # ================== USER_ACTIONS ==================
    print("Sinh user_actions từ orders/ratings + view random...")

    # 1) Hành vi tương quan với orders: view, add_to_cart, purchase
    action_count = 0
    for od in orders:
        user_id = od["user_id"]
        order_date = od["order_date"]
        for b in od["books"]:
            book_id = b["book_id"]

            # giả định user VIEW sách vài phút trước khi mua
            view_time = order_date - timedelta(minutes=random.randint(5, 60))
            cursor.execute(
                """
                INSERT INTO user_actions
                    (user_id, book_id, action_type, metadata, action_date)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, book_id, "view",
                 json.dumps({"source": "auto", "stage": "pre_order"}),
                 view_time)
            )
            action_count += 1

            # add_to_cart
            atc_time = order_date - timedelta(minutes=random.randint(1, 30))
            cursor.execute(
                """
                INSERT INTO user_actions
                    (user_id, book_id, action_type, metadata, action_date)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, book_id, "add_to_cart",
                 json.dumps({"source": "auto"}),
                 atc_time)
            )
            action_count += 1

            # purchase
            cursor.execute(
                """
                INSERT INTO user_actions
                    (user_id, book_id, action_type, metadata, action_date)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, book_id, "purchase",
                 json.dumps({"order_id": od["order_id"]}),
                 order_date)
            )
            action_count += 1

    conn.commit()

    # 2) Thêm một số hành vi view, click, wishlist rải rác
    for user_id in users:
        # random view
        for _ in range(EXTRA_VIEW_ACTIONS_PER_USER):
            b = random.choice(books)
            book_id = b["book_id"]
            act_time = random_past_datetime(days=365)
            act_type = rand_choice_weighted([
                ("view", 0.6),
                ("click", 0.2),
                ("wishlist", 0.2),
            ])
            cursor.execute(
                """
                INSERT INTO user_actions
                    (user_id, book_id, action_type, metadata, action_date)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, book_id, act_type,
                 json.dumps({"source": "random"}),
                 act_time)
            )
            action_count += 1

    conn.commit()

    print(f"Đã tạo khoảng {action_count} user_actions.")

    # ================== ACCESS_KEYS (tùy chọn) ==================
    print("Sinh access_keys cơ bản...")
    for user_id in users:
        if random.random() < 0.7:
            # 1–2 device
            num_devices = random.randint(1, 2)
            for _ in range(num_devices):
                access_token = "".join(random.choices(
                    string.ascii_letters + string.digits, k=40))
                refresh_token = "".join(random.choices(
                    string.ascii_letters + string.digits, k=40))
                device_info = random_device()
                ip_address = random_ip()
                expires_at = datetime.now() + timedelta(days=random.randint(1, 60))

                cursor.execute(
                    """
                    INSERT INTO access_keys
                        (user_id, access_token, refresh_token,
                         device_info, ip_address, expires_at)
                    VALUES (%s, %s, %s,
                            %s, %s, %s)
                    """,
                    (user_id, access_token, refresh_token,
                     device_info, ip_address, expires_at)
                )
        conn.commit()

    print("Hoàn tất sinh dữ liệu giả cho các bảng nghiệp vụ.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
