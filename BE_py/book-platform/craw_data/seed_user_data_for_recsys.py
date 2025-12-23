import os
import random
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional

import mysql.connector
from mysql.connector import Error

# Nếu bạn dùng file .env thì cài:
# pip install python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Không sao, sẽ dùng trực tiếp biến môi trường của hệ thống
    pass


# ================== CẤU HÌNH & TARGET ==================

BASE_DIR = Path(__file__).resolve().parent

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DB", "bookstore"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
}

# Tổng số user (bao gồm admin + staff + customer)
TARGET_USERS = 300

# Phân bổ role
NUM_ADMINS = 2
NUM_STAFF = 8  # muốn nhiều staff hơn thì tăng số này

# customer = TARGET_USERS - NUM_ADMINS - NUM_STAFF

TARGET_ADDRESSES = 500
TARGET_CART_ITEMS = 1000
TARGET_WISHLIST_ITEMS = 3000
TARGET_ORDERS = 3000
TARGET_ORDER_DETAILS = 5000
TARGET_PAYMENTS = 1000
TARGET_PROMOTIONS = 100
TARGET_RATINGS = 3000
TARGET_USER_ACTIONS = 20000
TARGET_ACCESS_KEYS = 500
TARGET_RECOMMENDATIONS_PER_USER = 0  # tạm thời không seed bảng recommendations


# ================== HÀM CƠ BẢN ==================

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            print("✅ Kết nối MySQL thành công.")
            return conn
    except Error as e:
        print("❌ Lỗi kết nối MySQL:", e)
    return None


def random_past_datetime(days_back: int = 365) -> datetime:
    """Random một thời điểm trong quá khứ `days_back` ngày."""
    now = datetime.now()
    delta_days = random.randint(0, days_back)
    delta_sec = random.randint(0, 24 * 3600)
    return now - timedelta(days=delta_days, seconds=delta_sec)


# ================== HELPER TẠO DỮ LIỆU THỰC TẾ HƠN ==================

def generate_vn_address() -> str:
    """Sinh địa chỉ kiểu Việt Nam tương đối thực tế."""
    cities = [
        {
            "name": "TP. Hồ Chí Minh",
            "districts": [
                "Quận 1", "Quận 3", "Quận 5", "Quận 7", "Quận 10",
                "Bình Thạnh", "Tân Bình", "Gò Vấp", "Phú Nhuận", "Thủ Đức",
            ],
        },
        {
            "name": "Hà Nội",
            "districts": [
                "Ba Đình", "Hoàn Kiếm", "Hai Bà Trưng", "Đống Đa",
                "Cầu Giấy", "Thanh Xuân", "Nam Từ Liêm", "Bắc Từ Liêm",
            ],
        },
        {
            "name": "Đà Nẵng",
            "districts": ["Hải Châu", "Thanh Khê", "Liên Chiểu", "Sơn Trà", "Cẩm Lệ"],
        },
        {
            "name": "Cần Thơ",
            "districts": ["Ninh Kiều", "Bình Thủy", "Cái Răng"],
        },
        {
            "name": "Hải Phòng",
            "districts": ["Hồng Bàng", "Ngô Quyền", "Lê Chân"],
        },
    ]

    streets = [
        "Nguyễn Huệ", "Lê Lợi", "Trần Hưng Đạo", "Lý Thường Kiệt",
        "Nguyễn Trãi", "Phạm Ngũ Lão", "Cách Mạng Tháng 8", "Điện Biên Phủ",
        "Hoàng Diệu", "Võ Văn Tần", "Nguyễn Thị Minh Khai",
    ]

    building_prefix = [
        "Chung cư", "Tòa nhà", "Khu dân cư", "Khu căn hộ",
        "Nhà riêng", "Nhà trọ", "Khu đô thị",
    ]

    city = random.choice(cities)
    city_name = city["name"]
    district = random.choice(city["districts"])
    ward_no = random.randint(1, 15)
    ward = f"Phường {ward_no}"
    street = random.choice(streets)
    house_no = random.randint(1, 999)

    # Ngẫu nhiên có thêm tên tòa nhà/khu
    if random.random() < 0.3:
        b_prefix = random.choice(building_prefix)
        b_name = f"{b_prefix} {random.randint(1, 20)}"
        return f"{b_name}, Số {house_no} {street}, {ward}, {district}, {city_name}"
    else:
        return f"Số {house_no} {street}, {ward}, {district}, {city_name}"


def generate_review_text(rating: int) -> str:
    """Sinh câu review tiếng Việt hợp lý theo số sao."""
    rating = int(rating)

    templates_5 = [
        "Sách rất hay, nội dung sâu sắc và dễ hiểu, đọc xong thấy học được rất nhiều.",
        "Rất hài lòng, trình bày rõ ràng, ví dụ minh họa thực tế, đáng tiền.",
        "Một trong những cuốn sách hay nhất mình từng đọc, phù hợp để đọc đi đọc lại.",
    ]
    templates_4 = [
        "Sách khá hay, nội dung hữu ích, chỉ là cách trình bày hơi dài dòng.",
        "Nội dung tốt, có nhiều kiến thức thực tế, nhìn chung rất đáng mua.",
        "Sách ổn, nhiều thông tin mới, nhưng nếu biên tập lại gọn hơn thì tuyệt.",
    ]
    templates_3 = [
        "Nội dung ở mức ổn, có vài phần trùng lặp và hơi lan man.",
        "Một số chương khá hay nhưng tổng thể chưa thực sự ấn tượng.",
        "Sách bình thường, đọc giải trí được, chưa có nhiều điểm đặc biệt.",
    ]
    templates_2 = [
        "Không đúng kỳ vọng, nội dung khá hời hợt và ít ví dụ thực tế.",
        "Sách trình bày khó theo dõi, nhiều chỗ cảm giác bị kéo dài không cần thiết.",
    ]
    templates_1 = [
        "Không recommend, nội dung rời rạc và rất khó nắm ý chính.",
        "Mua về hơi thất vọng, gần như không áp dụng được gì.",
    ]

    if rating >= 5:
        return random.choice(templates_5)
    if rating == 4:
        return random.choice(templates_4)
    if rating == 3:
        return random.choice(templates_3)
    if rating == 2:
        return random.choice(templates_2)
    return random.choice(templates_1)


# ================== METADATA BUILDER CHO USER_ACTIONS ==================

def build_metadata(
    action_type: str,
    session_id: str,
    extra: Optional[Dict[str, Any]] = None
) -> str:
    """
    Tạo metadata JSON cho user_actions.
    Có các field chung: session_id, device, platform.
    Thêm extra tùy theo action_type.
    """
    base: Dict[str, Any] = {
        "session_id": session_id,
        "device": random.choice(["desktop", "mobile"]),
        "platform": "web",
    }
    if extra:
        base.update(extra)
    return json.dumps(base, ensure_ascii=False)


# ================== XÓA DATA CŨ USER-RELATED ==================

def clear_user_related_data(conn):
    cursor = conn.cursor()
    print("🔄 Đang xóa dữ liệu user-related...")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    tables = [
        "order_details",
        "payments",
        "orders",
        "cart_items",
        "carts",
        "wishlist_items",
        "wishlists",
        "ratings",
        "user_actions",
        "recommendations",
        "access_keys",
        "addresses",
        "promotions",
        "users",
    ]

    for tbl in tables:
        print(f"  TRUNCATE TABLE {tbl}...")
        cursor.execute(f"TRUNCATE TABLE {tbl}")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    cursor.close()
    print("✅ Đã xóa dữ liệu cũ trong các bảng user-related.")


# ================== LẤY DANH SÁCH SÁCH ==================

def fetch_books(conn) -> List[Tuple[int, float]]:
    cursor = conn.cursor()
    cursor.execute("SELECT book_id, price FROM books WHERE status = 'active'")
    rows = cursor.fetchall()
    cursor.close()
    print(f"📚 Đã load {len(rows)} sách từ bảng books.")
    return rows


# ================== SEED USERS & ADDRESSES ==================

def seed_users_and_addresses(conn) -> Tuple[List[int], int]:
    """
    Tạo ~TARGET_USERS users:
      - NUM_ADMINS admin: admin01, admin02, ...
      - NUM_STAFF staff: staff01, staff02, ...
      - phần còn lại là customer: user001, user002, ...
    Mỗi user có ít nhất 1 địa chỉ default, sau đó thêm địa chỉ phụ tới ~TARGET_ADDRESSES.
    """
    cursor = conn.cursor()

    user_sql = """
        INSERT INTO users (username, email, password_hash, full_name, phone, role, status, is_deleted)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
    """

    users_data = []

    # ---- Admins ----
    for i in range(1, NUM_ADMINS + 1):
        username = f"admin{i:02d}"
        email = f"{username}@example.com"
        full_name = f"Admin {i:02d}"
        phone = f"0900{i:04d}"[:10]
        password_hash = "admin_hashed_password"
        users_data.append(
            (username, email, password_hash, full_name, phone, "admin", "active")
        )

    # ---- Staff ----
    for i in range(1, NUM_STAFF + 1):
        username = f"staff{i:02d}"
        email = f"{username}@example.com"
        full_name = f"Staff {i:02d}"
        phone = f"0901{i:04d}"[:10]
        password_hash = "staff_hashed_password"
        users_data.append(
            (username, email, password_hash, full_name, phone, "staff", "active")
        )

    # ---- Customers ----
    remaining_customers = max(TARGET_USERS - NUM_ADMINS - NUM_STAFF, 0)
    for i in range(1, remaining_customers + 1):
        username = f"user{i:03d}"
        email = f"{username}@example.com"
        full_name = f"User {i:03d}"
        phone = f"091{i:04d}"[:10]
        password_hash = "user_hashed_password"
        users_data.append(
            (username, email, password_hash, full_name, phone, "customer", "active")
        )

    cursor.executemany(user_sql, users_data)
    conn.commit()

    cursor.execute("SELECT user_id FROM users ORDER BY user_id")
    user_ids = [row[0] for row in cursor.fetchall()]
    print(
        f"👤 Đã tạo {len(user_ids)} users "
        f"(admins={NUM_ADMINS}, staff={NUM_STAFF}, customers={remaining_customers})."
    )

    # ---- Addresses ----
    addr_sql = """
        INSERT INTO addresses (user_id, address_text, is_default)
        VALUES (%s, %s, %s)
    """

    addr_data = []
    # Mỗi user 1 địa chỉ default (địa chỉ VN thực tế hơn)
    for uid in user_ids:
        addr_text = generate_vn_address()
        addr_data.append((uid, addr_text, 1))

    cursor.executemany(addr_sql, addr_data)
    conn.commit()
    base_addr_count = len(addr_data)

    # Thêm address phụ để gần TARGET_ADDRESSES
    extra_to_create = max(TARGET_ADDRESSES - base_addr_count, 0)
    extra_addr_data = []
    for _ in range(extra_to_create):
        uid = random.choice(user_ids)
        addr_text = generate_vn_address()
        extra_addr_data.append((uid, addr_text, 0))

    if extra_addr_data:
        cursor.executemany(addr_sql, extra_addr_data)
        conn.commit()

    total_addr = base_addr_count + len(extra_addr_data)
    print(
        f"🏠 Đã tạo tổng cộng {total_addr} addresses (target ~{TARGET_ADDRESSES}).")

    cursor.close()
    return user_ids, total_addr


# ================== SEED CARTS & WISHLISTS ==================

def seed_carts_and_wishlists(conn, user_ids: List[int]):
    cursor = conn.cursor()

    cart_sql = "INSERT INTO carts (user_id) VALUES (%s)"
    wl_sql = "INSERT INTO wishlists (user_id) VALUES (%s)"

    cart_data = [(uid,) for uid in user_ids]
    wl_data = [(uid,) for uid in user_ids]

    cursor.executemany(cart_sql, cart_data)
    cursor.executemany(wl_sql, wl_data)
    conn.commit()

    cursor.execute("SELECT cart_id, user_id FROM carts")
    cart_map = {uid: cid for (cid, uid) in cursor.fetchall()}

    cursor.execute("SELECT wishlist_id, user_id FROM wishlists")
    wl_map = {uid: wid for (wid, uid) in cursor.fetchall()}

    cursor.close()

    print(f"🛒 Đã tạo {len(cart_map)} carts (1 cart / user).")
    print(f"📜 Đã tạo {len(wl_map)} wishlists (1 wishlist / user).")
    return cart_map, wl_map


# ================== SEED PROMOTIONS ==================

def seed_promotions(conn):
    cursor = conn.cursor()

    promo_sql = """
        INSERT INTO promotions
        (code, discount_percent, start_date, end_date, is_active, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    today = datetime.now().date()
    promo_data = []
    for i in range(1, TARGET_PROMOTIONS + 1):
        code = f"SALE{i:03d}"
        discount = random.choice([5.0, 10.0, 15.0, 20.0, 25.0])
        start_date = today - timedelta(days=random.randint(0, 120))
        end_date = start_date + timedelta(days=random.randint(7, 90))
        is_active = 1 if end_date >= today else 0
        status = "active" if is_active else "inactive"
        promo_data.append((code, discount, start_date,
                          end_date, is_active, status))

    cursor.executemany(promo_sql, promo_data)
    conn.commit()

    cursor.execute("SELECT promo_id FROM promotions")
    promo_ids = [row[0] for row in cursor.fetchall()]

    cursor.close()
    print(
        f"🎟️  Đã tạo {len(promo_ids)} promotions (target {TARGET_PROMOTIONS}).")
    return promo_ids


# ================== SEED CART_ITEMS & WISHLIST_ITEMS ==================

def seed_cart_and_wishlist_items(
    conn,
    user_ids: List[int],
    cart_map: Dict[int, int],
    wl_map: Dict[int, int],
    books: List[Tuple[int, float]],
):
    if not books:
        print("❌ Không có sách, bỏ seed cart_items/wishlist_items.")
        return

    cursor = conn.cursor()

    cart_item_sql = """
        INSERT INTO cart_items (cart_id, book_id, quantity)
        VALUES (%s, %s, %s)
    """
    wl_item_sql = """
        INSERT INTO wishlist_items (wishlist_id, book_id)
        VALUES (%s, %s)
    """

    # Unique (cart_id, book_id) pairs
    cart_pairs = set()
    max_cart_pairs = min(TARGET_CART_ITEMS, len(cart_map) * max(1, len(books)))
    while len(cart_pairs) < max_cart_pairs:
        uid = random.choice(user_ids)
        cart_id = cart_map.get(uid)
        if not cart_id:
            continue
        book_id, _ = random.choice(books)
        cart_pairs.add((cart_id, book_id))

    cart_items_data = [(cid, bid, random.randint(1, 3))
                       for (cid, bid) in cart_pairs]

    # Unique (wishlist_id, book_id) pairs
    wl_pairs = set()
    max_wl_pairs = min(TARGET_WISHLIST_ITEMS, len(wl_map) * max(1, len(books)))
    while len(wl_pairs) < max_wl_pairs:
        uid = random.choice(user_ids)
        wl_id = wl_map.get(uid)
        if not wl_id:
            continue
        book_id, _ = random.choice(books)
        wl_pairs.add((wl_id, book_id))

    wl_items_data = [(wid, bid) for (wid, bid) in wl_pairs]

    if cart_items_data:
        cursor.executemany(cart_item_sql, cart_items_data)
    if wl_items_data:
        cursor.executemany(wl_item_sql, wl_items_data)
    conn.commit()
    cursor.close()

    print(
        f"🛍️  Đã tạo {len(cart_items_data)} cart_items (target ~{TARGET_CART_ITEMS})."
    )
    print(
        f"💗 Đã tạo {len(wl_items_data)} wishlist_items (target ~{TARGET_WISHLIST_ITEMS})."
    )


# ================== SEED ORDERS, ORDER_DETAILS, PAYMENTS ==================

def seed_orders_payments(
    conn,
    user_ids: List[int],
    books: List[Tuple[int, float]],
    promo_ids: List[int],
):
    if not books:
        print("❌ Không có sách, bỏ seed orders.")
        return

    cursor = conn.cursor()

    order_sql = """
        INSERT INTO orders
        (user_id, address_id, promo_id, order_date, status,
         payment_method, payment_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    od_sql = """
        INSERT INTO order_details
        (order_id, book_id, quantity, unit_price, total_price)
        VALUES (%s, %s, %s, %s, %s)
    """
    pay_sql = """
        INSERT INTO payments
        (order_id, amount, provider, transaction_id, status)
        VALUES (%s, %s, %s, %s, %s)
    """

    # Map addresses theo user
    cursor.execute("SELECT user_id, address_id FROM addresses")
    addr_map: Dict[int, List[int]] = {}
    for uid, addr_id in cursor.fetchall():
        addr_map.setdefault(uid, []).append(addr_id)

    orders_count = 0
    details_count = 0
    payments_count = 0

    print("📦 Đang tạo orders + order_details + payments...")

    user_index = 0
    num_users = len(user_ids)

    while orders_count < TARGET_ORDERS and details_count < TARGET_ORDER_DETAILS:
        uid = user_ids[user_index]
        user_index = (user_index + 1) % num_users

        # random bỏ qua một số lần để phân tán
        if random.random() < 0.2:
            continue

        addr_ids = addr_map.get(uid)
        if not addr_ids:
            continue
        address_id = random.choice(addr_ids)

        order_date = random_past_datetime(365)
        status = random.choices(
            ["pending", "processing", "shipped",
                "delivered", "cancelled", "returned"],
            weights=[1, 2, 3, 4, 5, 6],
            k=1,
        )[0]
        payment_method = random.choice(["COD", "CreditCard", "E-Wallet"])
        payment_status = "paid" if status in (
            "shipped", "delivered") else "unpaid"

        promo_id = None
        if promo_ids and random.random() < 0.3:
            promo_id = random.choice(promo_ids)

        # === insert order ===
        order_values = (
            uid,
            address_id,
            promo_id,
            order_date,
            status,
            payment_method,
            payment_status,
        )
        cursor.execute(order_sql, order_values)
        order_id = cursor.lastrowid
        orders_count += 1

        # === insert order_details (mỗi order không trùng book_id) ===
        num_items = random.randint(1, 5)
        used_book_ids = set()

        for _ in range(num_items):
            if details_count >= TARGET_ORDER_DETAILS:
                break

            # lấy ngẫu nhiên 1 sách (book_id, price)
            tries = 0
            book_id = None
            book_price = None

            while tries < 10:
                candidate_book_id, candidate_price = random.choice(books)
                if candidate_book_id not in used_book_ids:
                    book_id = candidate_book_id
                    book_price = candidate_price
                    used_book_ids.add(book_id)
                    break
                tries += 1

            if book_id is None:
                continue  # không tìm được sách mới cho order này

            quantity = random.randint(1, 5)

            # ---- unit_price lấy từ price của books ----
            base_price = float(book_price or 0)
            if base_price <= 0:
                # fallback nếu dữ liệu books không hợp lệ
                base_price = random.randint(30, 250) * 1000

            # cho đẹp thì làm tròn theo 1.000
            unit_price = round(base_price / 1000) * 1000
            line_total = unit_price * quantity

            cursor.execute(
                od_sql, (order_id, book_id, quantity, unit_price, line_total)
            )
            details_count += 1

        # === insert payment ===
        if payments_count < TARGET_PAYMENTS and status != "cancelled":
            cursor.execute(
                "SELECT SUM(total_price) FROM order_details WHERE order_id = %s",
                (order_id,),
            )
            total_amount = cursor.fetchone()[0] or 0.0

            provider = (
                "Momo"
                if payment_method == "E-Wallet"
                else "Napass"
                if payment_method == "CreditCard"
                else "COD"
            )
            tx_id = f"TX{order_id:06d}"
            pay_status = "success" if payment_status == "paid" else "pending"

            cursor.execute(
                pay_sql, (order_id, total_amount, provider, tx_id, pay_status)
            )
            payments_count += 1

    conn.commit()
    cursor.close()

    print(
        f"✅ Đã tạo {orders_count} orders (target {TARGET_ORDERS}), "
        f"{details_count} order_details (target {TARGET_ORDER_DETAILS}), "
        f"{payments_count} payments (target {TARGET_PAYMENTS})."
    )


# ================== SEED RATINGS ==================

def seed_ratings(conn, user_ids: List[int], books: List[Tuple[int, float]]):
    if not books:
        print("❌ Không có sách, bỏ seed ratings.")
        return

    cursor = conn.cursor()

    rating_sql = """
        INSERT INTO ratings (user_id, book_id, rating, review, status)
        VALUES (%s, %s, %s, %s, %s)
    """

    pairs = set()
    max_pairs = min(TARGET_RATINGS, len(user_ids) * len(books))

    while len(pairs) < max_pairs:
        uid = random.choice(user_ids)
        book_id, _ = random.choice(books)
        pairs.add((uid, book_id))

    ratings_data = []
    for uid, book_id in pairs:
        rating = random.randint(3, 5)
        review = generate_review_text(rating)
        ratings_data.append((uid, book_id, rating, review, "approved"))

    if ratings_data:
        cursor.executemany(rating_sql, ratings_data)
    conn.commit()
    cursor.close()
    print(f"⭐ Đã tạo {len(ratings_data)} ratings (target {TARGET_RATINGS}).")


def rebuild_book_ratings(conn):
    """
    Tính lại avg_rating và rating_count trong bảng books
    dựa trên bảng ratings (status='approved').
    """
    cursor = conn.cursor()
    sql = """
        UPDATE books b
        LEFT JOIN (
            SELECT 
                book_id,
                AVG(rating) AS avg_rating,
                COUNT(*)   AS rating_count
            FROM ratings
            WHERE status = 'approved'
            GROUP BY book_id
        ) r ON b.book_id = r.book_id
        SET 
            b.avg_rating   = IFNULL(r.avg_rating, 0),
            b.rating_count = IFNULL(r.rating_count, 0)
    """
    cursor.execute(sql)
    conn.commit()
    cursor.close()
    print("✅ Đã cập nhật avg_rating, rating_count từ bảng ratings.")


# ================== SEED USER_ACTIONS ==================

def seed_user_actions(conn, user_ids: List[int], books: List[Tuple[int, float]]):
    if not books:
        print("❌ Không có sách, bỏ seed user_actions.")
        return

    cursor = conn.cursor()

    ua_sql = """
        INSERT INTO user_actions (user_id, book_id, action_type, metadata, action_date)
        VALUES (%s, %s, %s, %s, %s)
    """

    # action_types = ["view", "add_to_cart", "purchase", "wishlist", "click"]
    action_types = ["view", "add_to_cart", "purchase"]
    actions_data = []
    total = 0
    print("👣 Đang tạo user_actions...")

    while total < TARGET_USER_ACTIONS:
        uid = random.choice(user_ids)
        book_id, price = random.choice(books)
        action_type = random.choice(action_types)
        action_date = random_past_datetime(180)

        # session id giả lập
        session_id = f"sess_{uid}_{random.randint(1000, 9999)}"

        if action_type == "view":
            meta = build_metadata(
                "view",
                session_id,
                {
                    "source": random.choice(
                        ["home", "search", "category", "recommendation"]
                    ),
                    "list_type": random.choice(
                        ["home_reco", "search_result", "category", "similar_books"]
                    ),
                    "position": random.randint(1, 20),
                    "view_type": random.choice(["detail", "quick_view"]),
                },
            )
        elif action_type == "add_to_cart":
            meta = build_metadata(
                "add_to_cart",
                session_id,
                {
                    "cart_id": random.randint(1, 1000),
                    "quantity": random.randint(1, 3),
                    "price_at_add": float(price),
                    "from_reco": random.random() < 0.4,
                    "reco_algo": random.choice(["CF", "CB", "Hybrid"]),
                },
            )
        elif action_type == "purchase":
            meta = build_metadata(
                "purchase",
                session_id,
                {
                    "order_id": random.randint(1, TARGET_ORDERS),
                    "quantity": random.randint(1, 3),
                    "price_at_purchase": float(price),
                    "payment_method": random.choice(["COD", "CreditCard", "E-Wallet"]),
                },
            )
        elif action_type == "wishlist":
            meta = build_metadata(
                "wishlist",
                session_id,
                {
                    "wishlist_id": random.randint(1, 1000),
                    "reason": random.choice(
                        ["save_for_later", "favorite_author", "interesting_cover"]
                    ),
                },
            )
        else:  # click
            meta = build_metadata(
                "click",
                session_id,
                {
                    "target_type": random.choice(
                        ["recommendation", "banner", "category"]
                    ),
                    "block": random.choice(
                        ["home_you_may_like", "home_top_banner", "similar_books"]
                    ),
                    "position": random.randint(1, 10),
                },
            )

        actions_data.append((uid, book_id, action_type, meta, action_date))
        total += 1

    cursor.executemany(ua_sql, actions_data)
    conn.commit()
    cursor.close()
    print(f"✅ Đã tạo {total} user_actions (target {TARGET_USER_ACTIONS}).")


# ================== SEED ACCESS_KEYS ==================

def seed_access_keys(conn, user_ids: List[int]):
    cursor = conn.cursor()

    ak_sql = """
        INSERT INTO access_keys
        (user_id, access_token, refresh_token, device_info, ip_address, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    ak_data = []
    total = 0
    print("🔑 Đang tạo access_keys...")

    while total < TARGET_ACCESS_KEYS:
        uid = random.choice(user_ids)
        access_token = f"access_{uid}_{random.randint(100000,999999)}"
        refresh_token = f"refresh_{uid}_{random.randint(100000,999999)}"
        device_info = random.choice(
            ["Chrome on Windows", "Safari on iOS",
                "Chrome on Android", "Firefox on Linux"]
        )
        ip_address = f"192.168.1.{random.randint(2,254)}"
        expires_at = datetime.now() + timedelta(days=random.randint(7, 60))
        ak_data.append(
            (uid, access_token, refresh_token, device_info, ip_address, expires_at)
        )
        total += 1

    cursor.executemany(ak_sql, ak_data)
    conn.commit()
    cursor.close()
    print(f"✅ Đã tạo {total} access_keys (target {TARGET_ACCESS_KEYS}).")


# ================== MAIN ==================

def main():
    conn = get_connection()
    if not conn:
        return

    try:
        # 1) Xóa data cũ user-related
        clear_user_related_data(conn)

        # 2) Lấy list sách
        books = fetch_books(conn)
        if not books:
            print("⚠️ Không có sách nào. Hãy chạy insert_books_from_excel.py trước.")
            return

        # 3) Seed users + addresses
        user_ids, total_addr = seed_users_and_addresses(conn)

        # 4) Seed carts + wishlists
        cart_map, wl_map = seed_carts_and_wishlists(conn, user_ids)

        # 5) Seed cart_items + wishlist_items
        seed_cart_and_wishlist_items(conn, user_ids, cart_map, wl_map, books)

        # 6) Seed promotions
        promo_ids = seed_promotions(conn)

        # 7) Seed orders + order_details + payments
        seed_orders_payments(conn, user_ids, books, promo_ids)

        # 8) Seed ratings
        seed_ratings(conn, user_ids, books)

        # 8.1) Cập nhật lại avg_rating + rating_count trong bảng books
        rebuild_book_ratings(conn)

        # 9) Seed user_actions (có metadata thực tế hơn)
        seed_user_actions(conn, user_ids, books)

        # 10) Seed access_keys
        seed_access_keys(conn, user_ids)

        print("🎉 Hoàn tất seed data user-related cho hệ thống gợi ý.")

    finally:
        conn.close()
        print("🔌 Đã đóng kết nối MySQL.")


if __name__ == "__main__":
    main()
