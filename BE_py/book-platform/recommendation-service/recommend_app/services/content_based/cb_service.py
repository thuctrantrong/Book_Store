from recommend_app.db import get_connection


def get_similar_books(book_id: int, limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT 
            sb.similar_book_id AS book_id,
            b.title,
            b.price,
            b.main_image,
            sb.score AS final_score,
            'cb_tfidf' AS reason
        FROM similar_books sb
        JOIN books b ON b.book_id = sb.similar_book_id
        WHERE sb.book_id = %s 
          AND sb.algo_type = 'TFIDF'
        ORDER BY sb.score DESC
        LIMIT %s
    """
    cursor.execute(sql, (book_id, limit))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return rows
