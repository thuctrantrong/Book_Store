use bookstore;
-- View tiện lợi cho sách
CREATE OR REPLACE VIEW vw_book_main AS
SELECT 
  t.book_id,
  t.title,
  t.price,
  t.avg_rating,
  t.rating_count,
  t.status,
  t.publication_year,
  t.format,
  t.main_image,
  t.author_name
FROM (
  SELECT 
    b.book_id,
    b.title,
    b.price,
    b.avg_rating,
    b.rating_count,
    b.status,
    b.publication_year,
    b.format,
    a.author_name AS author_name,
    bi.image_url AS main_image,
    ROW_NUMBER() OVER (
      PARTITION BY b.book_id
      ORDER BY bi.is_main DESC, bi.image_id ASC
    ) AS rn
  FROM books b
  LEFT JOIN authors a ON a.author_id = b.author_id
  LEFT JOIN book_images bi ON bi.book_id = b.book_id
  WHERE b.status='active' AND b.stock_quantity > 0
) t
WHERE t.rn = 1;





-- Test
select * from vw_book_main 
where main_image is not null
limit 10;


-- 1. Gợi ý Top sách bán chạy cho trang chủ
DELIMITER $$

CREATE PROCEDURE sp_recommend_popular(IN p_limit INT)
BEGIN
    SELECT 
          v.book_id,
		  v.title,
		  v.author_name,
		  v.price,
		  v.main_image,
		  v.avg_rating,
		  v.rating_count,
		  IFNULL(p.total_sold, 0) AS total_sold
    FROM vw_book_main v
    LEFT JOIN (
        SELECT 
            od.book_id,
            SUM(od.quantity) AS total_sold
        FROM order_details od
        JOIN orders o ON od.order_id = o.order_id
        WHERE o.status IN ('processing','shipped','delivered')
        GROUP BY od.book_id
    ) p ON v.book_id = p.book_id
    Where main_image is not null
    ORDER BY p.total_sold DESC
    LIMIT p_limit;
END $$

DELIMITER ;

-- Test
CALL sp_recommend_popular(20);




-- 2. Gợi ý “Sách giống cuốn này” (theo thể loại + tác giả)
DELIMITER $$

CREATE PROCEDURE sp_recommend_for_book_rule_based(
    IN p_book_id INT,
    IN p_limit INT
)
BEGIN
    SELECT 
          v.book_id,
		  v.title,
		  v.author_name,
		  v.price,
		  v.main_image,
		  v.avg_rating,
		  v.rating_count,
        GROUP_CONCAT(DISTINCT rec.reason ORDER BY rec.priority_score DESC) AS reasons,
        MAX(rec.priority_score) AS final_score
    FROM (
        -- 1. Cùng thể loại
        SELECT 
            bc2.book_id,
            'same_category' AS reason,
            COUNT(*) AS priority_score
        FROM book_categories bc1
        JOIN book_categories bc2 
            ON bc1.category_id = bc2.category_id
        WHERE bc1.book_id = p_book_id
          AND bc2.book_id <> p_book_id
        GROUP BY bc2.book_id

        UNION ALL

        -- 2. Cùng tác giả
        SELECT 
            b2.book_id,
            'same_author' AS reason,
            1 AS priority_score
        FROM books b1
        JOIN books b2
            ON b1.author_id = b2.author_id
        WHERE b1.book_id = p_book_id
          AND b2.book_id <> p_book_id
    ) AS rec
    JOIN vw_book_main v ON rec.book_id = v.book_id
    GROUP BY v.book_id, v.title, v.price, v.main_image
    ORDER BY final_score DESC
    LIMIT p_limit;
END $$

DELIMITER ;



-- Test
SELECT book_id, title FROM books LIMIT 5;
CALL sp_recommend_for_book_rule_based( 1, 10 );



DELIMITER $$
CREATE PROCEDURE sp_recommend_top_rated(IN p_limit INT)
BEGIN
  SELECT 
    v.book_id,
    v.title,
    v.author_name,
    v.price,
    v.main_image,
    v.avg_rating,
    v.rating_count
  FROM vw_book_main v
  WHERE v.rating_count >= 3
  ORDER BY v.avg_rating DESC, v.rating_count DESC
  LIMIT p_limit;
END $$
DELIMITER ;


CALL sp_recommend_top_rated(10);





-- 3. “Khách mua sách này cũng mua” (co-purchase)
-- Dùng tốt cho trang chi tiết sách & trang giỏ hàng.

DROP PROCEDURE IF EXISTS sp_recommend_also_bought_for_book;
DELIMITER $$


CREATE PROCEDURE sp_recommend_also_bought_for_book(
    IN p_book_id INT,
    IN p_limit INT
)
BEGIN
    -- 1) Co-purchase
    SELECT *
    FROM (
        SELECT 
            v.book_id,
            v.title,
            v.price,
            v.main_image,
            v.author_name,
			v.avg_rating,
			v.rating_count,
            co.cnt AS score,
            'also_bought' AS reason,
            1 AS priority
        FROM (
            SELECT 
                od2.book_id,
                COUNT(DISTINCT o.order_id) AS cnt
            FROM orders o
            JOIN order_details od1 ON o.order_id = od1.order_id
            JOIN order_details od2 ON o.order_id = od2.order_id
            WHERE o.status IN ('processing','shipped','delivered')
              AND od1.book_id = p_book_id
              AND od2.book_id <> p_book_id
            GROUP BY od2.book_id
        ) co
        JOIN vw_book_main v ON v.book_id = co.book_id
        WHERE v.main_image IS NOT NULL

        UNION ALL

        -- 2) Fallback: cùng thể loại (nếu co-purchase không đủ)
        SELECT 
            v.book_id,
            v.title,
            v.price,
            v.main_image,
            v.author_name,
			v.avg_rating,
			v.rating_count,
            sc.common_cat AS score,
            'same_category_fallback' AS reason,
            2 AS priority
        FROM (
            SELECT bc2.book_id, COUNT(*) AS common_cat
            FROM book_categories bc1
            JOIN book_categories bc2 ON bc1.category_id = bc2.category_id
            WHERE bc1.book_id = p_book_id
              AND bc2.book_id <> p_book_id
              AND bc2.book_id NOT IN (
                  SELECT od2.book_id
                  FROM orders o
                  JOIN order_details od1 ON o.order_id = od1.order_id
                  JOIN order_details od2 ON o.order_id = od2.order_id
                  WHERE o.status IN ('processing','shipped','delivered')
                    AND od1.book_id = p_book_id
                    AND od2.book_id <> p_book_id
                  GROUP BY od2.book_id
              )
            GROUP BY bc2.book_id
        ) sc
        JOIN vw_book_main v ON v.book_id = sc.book_id
        WHERE v.main_image IS NOT NULL

        UNION ALL

        -- 3) Fallback cuối: sách bán chạy (nếu vẫn thiếu)
        SELECT 
            v.book_id,
            v.title,
            v.price,
            v.main_image,
            v.author_name,
			v.avg_rating,
			v.rating_count,
            IFNULL(p.total_sold,0) AS score,
            'popular_fallback' AS reason,
            3 AS priority
        FROM vw_book_main v
        LEFT JOIN (
            SELECT od.book_id, SUM(od.quantity) AS total_sold
            FROM order_details od
            JOIN orders o ON od.order_id = o.order_id
            WHERE o.status IN ('processing','shipped','delivered')
            GROUP BY od.book_id
        ) p ON p.book_id = v.book_id
        WHERE v.book_id <> p_book_id
          AND v.main_image IS NOT NULL
          AND v.book_id NOT IN (
              -- loại hết những cuốn đã nằm trong co-purchase hoặc same-category
              SELECT x.book_id FROM (
                  SELECT od2.book_id AS book_id
                  FROM orders o
                  JOIN order_details od1 ON o.order_id = od1.order_id
                  JOIN order_details od2 ON o.order_id = od2.order_id
                  WHERE o.status IN ('processing','shipped','delivered')
                    AND od1.book_id = p_book_id
                    AND od2.book_id <> p_book_id
                  GROUP BY od2.book_id

                  UNION

                  SELECT bc2.book_id AS book_id
                  FROM book_categories bc1
                  JOIN book_categories bc2 ON bc1.category_id = bc2.category_id
                  WHERE bc1.book_id = p_book_id
                    AND bc2.book_id <> p_book_id
                  GROUP BY bc2.book_id
              ) x
          )
    ) t
    ORDER BY t.priority ASC, t.score DESC
    LIMIT p_limit;
END $$

DELIMITER ;




call sp_recommend_also_bought_for_book(3,10);




-- 4. Gợi ý “Trending / Hot tuần này” (theo view/click)

DELIMITER $$

DROP PROCEDURE IF EXISTS sp_recommend_trending_views $$
CREATE PROCEDURE sp_recommend_trending_views(
    IN p_days INT,
    IN p_limit INT
)
BEGIN
    SELECT 
	  v.book_id,
	  v.title,
	  v.author_name,
	  v.price,
	  v.main_image,
	  v.avg_rating,
	  v.rating_count,
	  ua.score AS trend_score
    FROM (
        SELECT 
            ua.book_id,
            SUM(CASE 
                  WHEN ua.action_type = 'view' THEN 1
                  WHEN ua.action_type = 'add_to_cart' THEN 3
                  ELSE 0
                END) AS score
        FROM user_actions ua
        WHERE ua.action_date >= NOW() - INTERVAL p_days DAY
        GROUP BY ua.book_id
    ) ua
    JOIN vw_book_main v ON v.book_id = ua.book_id
    WHERE v.main_image IS NOT NULL
    ORDER BY ua.score DESC
    LIMIT p_limit;
END $$

DELIMITER ;


-- → Top sách xem nhiều 7 ngày gần đây.
CALL sp_recommend_trending_views(30, 10);   


-- 5. Gợi ý sách tương tự (Content-based TF-IDF)


DROP PROCEDURE IF EXISTS sp_recommend_for_book_cb;
DELIMITER $$


CREATE PROCEDURE sp_recommend_for_book_cb(
    IN p_book_id INT,
    IN p_limit INT
)
BEGIN
    SELECT 
        v.book_id,
        v.title,
        v.price,
        v.main_image,
        v.author_name,
		v.avg_rating,
		v.rating_count,
        sb.score
    FROM similar_books sb
    JOIN vw_book_main v ON v.book_id = sb.similar_book_id
    WHERE sb.book_id = p_book_id
      AND sb.algo_type = 'TFIDF'
      AND v.main_image IS NOT NULL
    ORDER BY sb.score DESC
    LIMIT p_limit;
END $$

DELIMITER ;


call sp_recommend_for_book_cb(1,20);


-- 6. View đếm số lần user mua theo category
CREATE OR REPLACE VIEW vw_user_category_counts AS
SELECT 
    o.user_id,
    bc.category_id,
    SUM(od.quantity) AS cnt
FROM orders o
JOIN order_details od ON o.order_id = od.order_id
JOIN book_categories bc ON od.book_id = bc.book_id
WHERE o.status IN ('processing','shipped','delivered')
GROUP BY o.user_id, bc.category_id;


DELIMITER $$

DROP PROCEDURE IF EXISTS sp_recommend_for_user_rule_based $$
CREATE PROCEDURE sp_recommend_for_user_rule_based(
    IN p_user_id INT,
    IN p_limit INT
)
BEGIN
    -- Top 3 category user này hay mua nhất
    WITH top_cat AS (
        SELECT category_id
        FROM vw_user_category_counts
        WHERE user_id = p_user_id
        ORDER BY cnt DESC
        LIMIT 3
    ),
    book_sold AS (
        SELECT 
            od.book_id,
            SUM(od.quantity) AS total_sold
        FROM order_details od
        JOIN orders o ON o.order_id = od.order_id
        WHERE o.status IN ('processing','shipped','delivered')
        GROUP BY od.book_id
    )
    SELECT 
        v.book_id,
        v.title,
        v.price,
        v.main_image,
        v.author_name,
		v.avg_rating,
		v.rating_count,
        'popular_in_user_categories' AS reason,
        IFNULL(bs.total_sold, 0) AS total_sold
    FROM book_categories bc
    JOIN top_cat tc ON bc.category_id = tc.category_id
    JOIN vw_book_main v ON v.book_id = bc.book_id
    LEFT JOIN book_sold bs ON bs.book_id = v.book_id
    WHERE v.book_id NOT IN (
        SELECT od.book_id
        FROM orders o
        JOIN order_details od ON o.order_id = od.order_id
        WHERE o.user_id = p_user_id
          AND o.status IN ('processing','shipped','delivered')
    )
    ORDER BY bs.total_sold DESC
    LIMIT p_limit;
END $$

DELIMITER ;

SELECT DISTINCT user_id FROM orders LIMIT 5;
CALL sp_recommend_for_user_rule_based(1, 10);









-- Trigger auto-clear khi update sách
DROP TRIGGER IF EXISTS trg_books_after_update_clear_cb;
DELIMITER $$

CREATE TRIGGER trg_books_after_update_clear_cb
AFTER UPDATE ON books
FOR EACH ROW
BEGIN
  IF NEW.title <> OLD.title
     OR IFNULL(NEW.description,'') <> IFNULL(OLD.description,'')
     OR IFNULL(NEW.author_id,0) <> IFNULL(OLD.author_id,0)
     OR IFNULL(NEW.publisher_id,0) <> IFNULL(OLD.publisher_id,0)
     OR IFNULL(NEW.language,'') <> IFNULL(OLD.language,'')
     OR IFNULL(NEW.format,'') <> IFNULL(OLD.format,'')
     OR IFNULL(NEW.publication_year,0) <> IFNULL(OLD.publication_year,0)
     OR NEW.status <> OLD.status
     OR NEW.stock_quantity <> OLD.stock_quantity
  THEN
     DELETE FROM similar_books
     WHERE book_id = NEW.book_id OR similar_book_id = NEW.book_id;
  END IF;
END $$

DELIMITER ;



DROP PROCEDURE IF EXISTS sp_recommend_for_book_cb_with_fallback;
DELIMITER $$

CREATE PROCEDURE sp_recommend_for_book_cb_with_fallback(
  IN p_book_id INT,
  IN p_limit INT
)
BEGIN
  WITH
  cb AS (
    SELECT
      v.book_id, v.title, v.price, v.main_image,
      v.author_name,
	  v.avg_rating,
	  v.rating_count,
      sb.score,
      1 AS priority,
      'TFIDF' AS reason
    FROM similar_books sb
    JOIN vw_book_main v ON v.book_id = sb.similar_book_id
    WHERE sb.book_id = p_book_id
      AND sb.algo_type = 'TFIDF'
      AND v.main_image IS NOT NULL
    ORDER BY sb.score DESC
    LIMIT p_limit
  ),
  rb_base AS (
    SELECT
      v.book_id, v.title, v.price, v.main_image,v.author_name,
		v.avg_rating,
		v.rating_count,
      MAX(rec.priority_score) AS score
    FROM (
      -- same category (nặng điểm hơn)
      SELECT bc2.book_id, COUNT(*)*2 AS priority_score
      FROM book_categories bc1
      JOIN book_categories bc2 ON bc1.category_id = bc2.category_id
      WHERE bc1.book_id = p_book_id
        AND bc2.book_id <> p_book_id
      GROUP BY bc2.book_id

      UNION ALL

      -- same author
      SELECT b2.book_id, 5 AS priority_score
      FROM books b1
      JOIN books b2 ON b1.author_id = b2.author_id
      WHERE b1.book_id = p_book_id
        AND b2.book_id <> p_book_id
    ) rec
    JOIN vw_book_main v ON v.book_id = rec.book_id
    WHERE v.main_image IS NOT NULL
    GROUP BY v.book_id, v.title, v.price, v.main_image
  ),
  rb AS (
    SELECT
      t.book_id, t.title, t.price, t.main_image,  t.author_name,
		t.avg_rating,
		t.rating_count, 
      t.score,
      2 AS priority,
      'RULE_BASED' AS reason
    FROM rb_base t
    WHERE t.book_id NOT IN (SELECT book_id FROM cb)
    ORDER BY t.score DESC
    LIMIT p_limit
  ),
  pop AS (
    SELECT
      v.book_id, v.title, v.price, v.main_image,v.author_name,
		v.avg_rating,
		v.rating_count,
      IFNULL(p.total_sold,0) AS score,
      3 AS priority,
      'POPULAR' AS reason
    FROM vw_book_main v
    LEFT JOIN (
      SELECT od.book_id, SUM(od.quantity) AS total_sold
      FROM orders o
      JOIN order_details od ON o.order_id = od.order_id
      WHERE o.status IN ('processing','shipped','delivered')
      GROUP BY od.book_id
    ) p ON p.book_id = v.book_id
    WHERE v.book_id <> p_book_id
      AND v.main_image IS NOT NULL
      AND v.book_id NOT IN (SELECT book_id FROM cb)
      AND v.book_id NOT IN (SELECT book_id FROM rb)
    ORDER BY score DESC
    LIMIT p_limit
  )
  SELECT book_id, title, price, main_image,author_name,
		avg_rating,
		rating_count, score, reason
  FROM (
    SELECT * FROM cb
    UNION ALL
    SELECT * FROM rb
    UNION ALL
    SELECT * FROM pop
  ) x
  ORDER BY priority ASC, score DESC
  LIMIT p_limit;

END $$

DELIMITER ;


CALL sp_recommend_for_book_cb_with_fallback(2, 30);





DROP PROCEDURE IF EXISTS sp_clear_similar_cache_for_book;
DELIMITER $$

CREATE PROCEDURE sp_clear_similar_cache_for_book(IN p_book_id INT)
BEGIN
    DELETE FROM similar_books
    WHERE book_id = p_book_id
       OR similar_book_id = p_book_id;
END $$

DELIMITER ;



DELIMITER $$

DROP PROCEDURE IF EXISTS sp_update_book_rating $$
CREATE PROCEDURE sp_update_book_rating(IN p_book_id INT)
BEGIN
    -- Cập nhật avg_rating và rating_count từ bảng ratings (chỉ tính status='approved')
    UPDATE books b
    LEFT JOIN (
        SELECT 
            book_id,
            AVG(rating) AS avg_rating,
            COUNT(*)    AS rating_count
        FROM ratings
        WHERE book_id = p_book_id
          AND status = 'approved'
          AND rating IS NOT NULL
        GROUP BY book_id
    ) r ON b.book_id = r.book_id
    SET 
        b.avg_rating   = IFNULL(r.avg_rating, 0),
        b.rating_count = IFNULL(r.rating_count, 0)
    WHERE b.book_id = p_book_id;
END $$

DELIMITER ;


-- 2) Trigger AFTER INSERT
DELIMITER $$

DROP TRIGGER IF EXISTS trg_ratings_after_insert $$
CREATE TRIGGER trg_ratings_after_insert
AFTER INSERT ON ratings
FOR EACH ROW
BEGIN
    IF NEW.book_id IS NOT NULL THEN
        CALL sp_update_book_rating(NEW.book_id);
    END IF;
END $$

DELIMITER ;



-- 3) Trigger AFTER UPDATE
DELIMITER $$

DROP TRIGGER IF EXISTS trg_ratings_after_update $$
CREATE TRIGGER trg_ratings_after_update
AFTER UPDATE ON ratings
FOR EACH ROW
BEGIN
    -- Nếu đổi book_id (hiếm)
    IF OLD.book_id IS NOT NULL THEN
        CALL sp_update_book_rating(OLD.book_id);
    END IF;

    IF NEW.book_id IS NOT NULL AND NEW.book_id <> OLD.book_id THEN
        CALL sp_update_book_rating(NEW.book_id);
    END IF;
END $$

DELIMITER ;




-- 4) Trigger AFTER DELETE
DELIMITER $$

DROP TRIGGER IF EXISTS trg_ratings_after_delete $$
CREATE TRIGGER trg_ratings_after_delete
AFTER DELETE ON ratings
FOR EACH ROW
BEGIN
    IF OLD.book_id IS NOT NULL THEN
        CALL sp_update_book_rating(OLD.book_id);
    END IF;
END $$

DELIMITER ;





-- Tạo procedure “Sách tương tự theo CF” (để dùng ở trang chi tiết sách)
DROP PROCEDURE IF EXISTS sp_recommend_for_book_cf;
DELIMITER $$

CREATE PROCEDURE sp_recommend_for_book_cf(
  IN p_book_id INT,
  IN p_algo VARCHAR(30),   -- 'CF_IMPLICIT' hoặc 'CF_PURCHASE'
  IN p_limit INT
)
BEGIN
  SELECT
    v.book_id,
    v.title,
    v.price,
    v.main_image,
    v.author_name,
	v.avg_rating,
	v.rating_count,
    sb.score
  FROM similar_books sb
  JOIN vw_book_main v ON v.book_id = sb.similar_book_id
  WHERE sb.book_id = p_book_id
    AND sb.algo_type = p_algo
    AND v.main_image IS NOT NULL
  ORDER BY sb.score DESC
  LIMIT p_limit;
END $$

DELIMITER ;


CALL sp_recommend_for_book_cf(2, 'CF_IMPLICIT', 10);


-- Procedure rebuild CF recommendations cho 1 user
DROP PROCEDURE IF EXISTS sp_rebuild_user_cf_implicit;
DELIMITER $$

CREATE PROCEDURE sp_rebuild_user_cf_implicit(
  IN p_user_id INT,
  IN p_days INT,
  IN p_topn INT
)
BEGIN
  DELETE FROM recommendations
  WHERE user_id = p_user_id AND algo_type = 'CF';

  INSERT INTO recommendations(user_id, book_id, score, rank_order, algo_type, explanation)
  SELECT user_id, book_id, score, rank_order, algo_type, explanation
  FROM (
    SELECT
      ua.user_id AS user_id,
      sb.similar_book_id AS book_id,

      -- normalized 0..100
      (SUM(ua.w * sb.score) / NULLIF(SUM(ua.w),0)) * 100 AS score,

      ROW_NUMBER() OVER (
        PARTITION BY ua.user_id
        ORDER BY (SUM(ua.w * sb.score) / NULLIF(SUM(ua.w),0)) DESC
      ) AS rank_order,

      'CF' AS algo_type,
      CONCAT('CF_IMPLICIT normalized from last ', p_days, ' days') AS explanation

    FROM (
      SELECT
        user_id,
        book_id,
        SUM(CASE
              WHEN action_type='view' THEN 1
              WHEN action_type='add_to_cart' THEN 3
              WHEN action_type='purchase' THEN 8
              ELSE 0
            END) AS w
      FROM user_actions
      WHERE user_id = p_user_id
        AND book_id IS NOT NULL
        AND action_date >= NOW() - INTERVAL p_days DAY
      GROUP BY user_id, book_id
      HAVING w > 0
    ) ua
    JOIN similar_books sb
      ON sb.book_id = ua.book_id
     AND sb.algo_type = 'CF_IMPLICIT'
    JOIN vw_book_main v
      ON v.book_id = sb.similar_book_id
    WHERE v.main_image IS NOT NULL
      AND sb.similar_book_id NOT IN (
        SELECT od.book_id
        FROM orders o
        JOIN order_details od ON o.order_id = od.order_id
        WHERE o.user_id = p_user_id
          AND o.status IN ('processing','shipped','delivered')
      )
    GROUP BY ua.user_id, sb.similar_book_id
  ) AS new_rows
  WHERE new_rows.rank_order <= p_topn
  ON DUPLICATE KEY UPDATE
    score = new_rows.score,
    rank_order = new_rows.rank_order,
    algo_type = new_rows.algo_type,
    explanation = new_rows.explanation;

END $$

DELIMITER ;


TRUNCATE TABLE recommendations;


CALL sp_rebuild_user_cf_implicit(1, 90, 50);

SELECT * FROM recommendations
WHERE user_id=1 AND algo_type='CF'
ORDER BY rank_order
LIMIT 20;






DROP PROCEDURE IF EXISTS sp_recommend_for_user_from_cache;
DELIMITER $$

CREATE PROCEDURE sp_recommend_for_user_from_cache(
  IN p_user_id INT,
  IN p_algo VARCHAR(10),   -- 'CF' hoặc 'Hybrid' hoặc 'CB'
  IN p_limit INT
)
BEGIN
  SELECT
    v.book_id,
    v.title,
    v.price,
    v.main_image,
    v.author_name,
	v.avg_rating,
	v.rating_count,
    r.score,
    r.rank_order,
    r.algo_type,
    r.explanation
  FROM recommendations r
  JOIN vw_book_main v ON v.book_id = r.book_id
  WHERE r.user_id = p_user_id
    AND r.algo_type = p_algo
    AND v.main_image IS NOT NULL
  ORDER BY r.rank_order ASC
  LIMIT p_limit;
END $$

DELIMITER ;

CALL sp_recommend_for_user_from_cache(1, 'CF', 20);



