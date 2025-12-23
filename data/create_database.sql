-- Tắt kiểm tra khóa ngoại tạm thời
SET FOREIGN_KEY_CHECKS = 0;

-- Xóa database cũ nếu đã tồn tại
DROP DATABASE IF EXISTS bookstore;

-- Tạo database mới
CREATE DATABASE IF NOT EXISTS bookstore
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Sử dụng database
USE bookstore;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS users;
CREATE TABLE users (
  user_id int NOT NULL AUTO_INCREMENT,
  username varchar(50) NOT NULL,
  email varchar(100) NOT NULL,
  password_hash varchar(255) NOT NULL,
  full_name varchar(100) DEFAULT NULL,
  phone varchar(20) DEFAULT NULL,
  role enum('customer','admin','staff') NOT NULL DEFAULT 'customer',
  status enum('unverified','active','locked') NOT NULL DEFAULT 'unverified',
  is_deleted tinyint(1) NOT NULL DEFAULT 0,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY username (username),
  UNIQUE KEY email (email)
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for addresses
-- ----------------------------
DROP TABLE IF EXISTS addresses;
CREATE TABLE addresses (
  address_id int NOT NULL AUTO_INCREMENT,
  user_id int DEFAULT NULL,
  address_text text NOT NULL,
  is_default tinyint(1) DEFAULT '0',
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (address_id),
  KEY user_id (user_id),
  CONSTRAINT addresses_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for authors
-- ----------------------------
DROP TABLE IF EXISTS authors;
CREATE TABLE authors (
  author_id int NOT NULL AUTO_INCREMENT,
  author_name varchar(256) NOT NULL,
  bio text,
  status enum('active','inactive','deleted') NOT NULL DEFAULT 'active',
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (author_id),
  UNIQUE KEY author_name (author_name)
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for publishers
-- ----------------------------
DROP TABLE IF EXISTS publishers;
CREATE TABLE publishers (
  publisher_id int NOT NULL AUTO_INCREMENT,
  publisher_name varchar(100) NOT NULL,
  status enum('active','inactive','deleted') NOT NULL DEFAULT 'active',
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (publisher_id),
  UNIQUE KEY publisher_name (publisher_name)
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for categories
-- ----------------------------
DROP TABLE IF EXISTS categories;
CREATE TABLE categories (
  category_id int NOT NULL AUTO_INCREMENT,
  category_name varchar(100) NOT NULL,
  status enum('active','inactive','deleted') NOT NULL DEFAULT 'active',
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (category_id),
  UNIQUE KEY category_name (category_name)
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for books
-- ----------------------------
DROP TABLE IF EXISTS books;
CREATE TABLE books (
  book_id int NOT NULL AUTO_INCREMENT,
  title varchar(255) NOT NULL,
  author_id int DEFAULT NULL,
  publisher_id int DEFAULT NULL,
  price decimal(10,2) NOT NULL,
  stock_quantity int NOT NULL,
  description text,
  publication_year int DEFAULT NULL,
  isbn varchar(13) DEFAULT NULL,
  avg_rating decimal(3,2) DEFAULT '0.00',
  rating_count int DEFAULT '0',
  language varchar(50) DEFAULT NULL,
  format enum('ebook','paperback','hardcover') NOT NULL,
  status enum('active','inactive','out_of_stock','deleted') NOT NULL DEFAULT 'active',
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (book_id),
  UNIQUE KEY isbn (isbn),
  KEY author_id (author_id),
  KEY publisher_id (publisher_id),
  FULLTEXT KEY idx_books_title_desc (title, description),
  CONSTRAINT books_ibfk_1 FOREIGN KEY (author_id) REFERENCES authors (author_id) ON DELETE SET NULL,
  CONSTRAINT books_ibfk_2 FOREIGN KEY (publisher_id) REFERENCES publishers (publisher_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for book_categories
-- ----------------------------
DROP TABLE IF EXISTS book_categories;
CREATE TABLE book_categories (
  book_id int NOT NULL,
  category_id int NOT NULL,
  PRIMARY KEY (book_id,category_id),
  KEY category_id (category_id),
  CONSTRAINT book_categories_ibfk_1 FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE,
  CONSTRAINT book_categories_ibfk_2 FOREIGN KEY (category_id) REFERENCES categories (category_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for book_images
-- ----------------------------
DROP TABLE IF EXISTS book_images;
CREATE TABLE book_images (
  image_id int NOT NULL AUTO_INCREMENT,
  book_id int DEFAULT NULL,
  image_url varchar(255) NOT NULL,
  is_main tinyint(1) DEFAULT '0',
  PRIMARY KEY (image_id),
  KEY book_id (book_id),
  CONSTRAINT book_images_ibfk_1 FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for carts
-- ----------------------------
DROP TABLE IF EXISTS carts;
CREATE TABLE carts (
  cart_id int NOT NULL AUTO_INCREMENT,
  user_id int DEFAULT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (cart_id),
  UNIQUE KEY user_id (user_id),
  CONSTRAINT carts_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for cart_items
-- ----------------------------
DROP TABLE IF EXISTS cart_items;
CREATE TABLE cart_items (
  cart_id int NOT NULL,
  book_id int NOT NULL,
  quantity int NOT NULL,
  PRIMARY KEY (cart_id,book_id),
  KEY book_id (book_id),
  CONSTRAINT cart_items_ibfk_1 FOREIGN KEY (cart_id) REFERENCES carts (cart_id) ON DELETE CASCADE,
  CONSTRAINT cart_items_ibfk_2 FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for wishlists
-- ----------------------------
DROP TABLE IF EXISTS wishlists;
CREATE TABLE wishlists (
  wishlist_id int NOT NULL AUTO_INCREMENT,
  user_id int DEFAULT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (wishlist_id),
  UNIQUE KEY user_id (user_id),
  CONSTRAINT wishlists_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for wishlist_items
-- ----------------------------
DROP TABLE IF EXISTS wishlist_items;
CREATE TABLE wishlist_items (
  wishlist_id int NOT NULL,
  book_id int NOT NULL,
  PRIMARY KEY (wishlist_id,book_id),
  KEY book_id (book_id),
  CONSTRAINT wishlist_items_ibfk_1 FOREIGN KEY (wishlist_id) REFERENCES wishlists (wishlist_id) ON DELETE CASCADE,
  CONSTRAINT wishlist_items_ibfk_2 FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for promotions
-- ----------------------------
DROP TABLE IF EXISTS promotions;
CREATE TABLE promotions (
  promo_id int NOT NULL AUTO_INCREMENT,
  code varchar(50) NOT NULL,
  discount_percent decimal(5,2) DEFAULT NULL,
  start_date date DEFAULT NULL,
  end_date date DEFAULT NULL,
  is_active tinyint(1) DEFAULT '1',
  status enum('active','inactive','deleted') NOT NULL DEFAULT 'active',
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (promo_id),
  UNIQUE KEY code (code)
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for orders
-- ----------------------------
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
  order_id int NOT NULL AUTO_INCREMENT,
  user_id int DEFAULT NULL,
  address_id int DEFAULT NULL,
  promo_id int DEFAULT NULL,
  order_date timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status enum('pending','processing','shipped','delivered','cancelled','returned') DEFAULT 'pending',
  payment_method enum('COD','CreditCard','E-Wallet') DEFAULT 'COD',
  payment_status enum('unpaid','paid','refunded') DEFAULT 'unpaid',
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (order_id),
  KEY user_id (user_id),
  KEY address_id (address_id),
  KEY promo_id (promo_id),
  CONSTRAINT orders_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL,
  CONSTRAINT orders_ibfk_2 FOREIGN KEY (address_id) REFERENCES addresses (address_id) ON DELETE SET NULL,
  CONSTRAINT orders_ibfk_3 FOREIGN KEY (promo_id) REFERENCES promotions (promo_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for order_details
-- ----------------------------
DROP TABLE IF EXISTS order_details;
CREATE TABLE order_details (
  order_id int NOT NULL,
  book_id int NOT NULL,
  quantity int NOT NULL,
  unit_price decimal(10,2) NOT NULL,
  total_price decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (order_id,book_id),
  KEY book_id (book_id),
  CONSTRAINT order_details_ibfk_1 FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE CASCADE,
  CONSTRAINT order_details_ibfk_2 FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for payments
-- ----------------------------
DROP TABLE IF EXISTS payments;
CREATE TABLE payments (
  payment_id int NOT NULL AUTO_INCREMENT,
  order_id int DEFAULT NULL,
  amount decimal(10,2) DEFAULT NULL,
  provider varchar(50) DEFAULT NULL,
  transaction_id varchar(100) DEFAULT NULL,
  status enum('success','failed','pending') DEFAULT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (payment_id),
  KEY order_id (order_id),
  CONSTRAINT payments_ibfk_1 FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for ratings
-- ----------------------------
DROP TABLE IF EXISTS ratings;
CREATE TABLE ratings (
  rating_id int NOT NULL AUTO_INCREMENT,
  user_id int DEFAULT NULL,
  book_id int DEFAULT NULL,
  rating int DEFAULT NULL,
  review text,
  status enum('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (rating_id),
  UNIQUE KEY user_id (user_id,book_id),
  KEY book_id (book_id),
  CONSTRAINT ratings_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
  CONSTRAINT ratings_ibfk_2 FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for user_actions
-- ----------------------------
DROP TABLE IF EXISTS user_actions;
CREATE TABLE user_actions (
  action_id int NOT NULL AUTO_INCREMENT,
  user_id int DEFAULT NULL,
  book_id int DEFAULT NULL,
  action_type enum('view','add_to_cart','purchase') NOT NULL,
  metadata json DEFAULT NULL,
  action_date timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (action_id),
  KEY user_id (user_id),
  KEY book_id (book_id),
  CONSTRAINT user_actions_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
  CONSTRAINT user_actions_ibfk_2 FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----------------------------
-- Table structure for recommendations
-- ----------------------------
DROP TABLE IF EXISTS recommendations;
CREATE TABLE recommendations (
  recommendation_id int NOT NULL AUTO_INCREMENT,
  user_id int DEFAULT NULL,
  book_id int DEFAULT NULL,
  score decimal(10,4) DEFAULT NULL,
  rank_order int DEFAULT NULL,
  algo_type enum('CF','CB','Hybrid') NOT NULL,
  explanation text,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (recommendation_id),
  KEY user_id (user_id),
  KEY book_id (book_id),
  CONSTRAINT recommendations_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
  CONSTRAINT recommendations_ibfk_2 FOREIGN KEY (book_id) REFERENCES books (book_id) ON DELETE CASCADE
) ENGINE=InnoDB;

ALTER TABLE recommendations
ADD UNIQUE KEY uq_user_book_algo (user_id, book_id, algo_type),
ADD INDEX idx_user_algo_rank (user_id, algo_type, rank_order);


-- ----------------------------
-- Table structure for access_keys
-- ----------------------------
DROP TABLE IF EXISTS access_keys;
CREATE TABLE access_keys (
  access_key_id int NOT NULL AUTO_INCREMENT,
  user_id int DEFAULT NULL,
  access_token varchar(255) NOT NULL,
  refresh_token varchar(255) DEFAULT NULL,
  device_info varchar(255) DEFAULT NULL,
  ip_address varchar(45) DEFAULT NULL,
  expires_at timestamp NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (access_key_id),
  KEY user_id (user_id),
  CONSTRAINT access_keys_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

DROP TABLE IF EXISTS similar_books;
CREATE TABLE IF NOT EXISTS similar_books (
    book_id INT NOT NULL,
    similar_book_id INT NOT NULL,
    score DECIMAL(6,4) NOT NULL,
    algo_type ENUM('TFIDF','HybridCB','CF_PURCHASE','CF_IMPLICIT') NOT NULL DEFAULT 'TFIDF',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (book_id, similar_book_id),
    CONSTRAINT fk_similar_books_book 
        FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    CONSTRAINT fk_similar_books_similar 
        FOREIGN KEY (similar_book_id) REFERENCES books(book_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- -------------------------------------------------
-- Thêm các index phục vụ analytics & recommendation
-- -------------------------------------------------
CREATE INDEX idx_user_actions_user_action_date
  ON user_actions(user_id, action_date);

CREATE INDEX idx_user_actions_book_action_type
  ON user_actions(book_id, action_type);

CREATE INDEX idx_ratings_book_id
  ON ratings(book_id);

CREATE INDEX idx_orders_user_date
  ON orders(user_id, order_date);
  
CREATE INDEX idx_user_actions_date_book
ON user_actions(action_date, book_id);


  
ALTER TABLE order_details
ADD COLUMN book_name VARCHAR(255) NOT NULL DEFAULT '' AFTER book_id;


UPDATE order_details od
JOIN books b ON od.book_id = b.book_id
SET od.book_name = b.title
WHERE od.book_name = '' OR od.book_name IS NULL;



UPDATE book_images
SET image_url = CONCAT('covers/books/', book_id, '/', image_id, '.jpg')
WHERE image_url IS NOT NULL
  AND image_url <> ''
  AND (image_url LIKE 'http://%' OR image_url LIKE 'https://%');
