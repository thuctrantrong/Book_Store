# CF hướng 1: Purchase-based (dựa vào orders)
import os
import mysql.connector
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from scipy import sparse
from sklearn.neighbors import NearestNeighbors

load_dotenv()
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "bookstore")


def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB
    )


def load_purchase_interactions():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT o.user_id, od.book_id, SUM(od.quantity) AS w
    FROM orders o
    JOIN order_details od ON o.order_id = od.order_id
    JOIN books b ON b.book_id = od.book_id
    WHERE o.status IN ('processing','shipped','delivered')
      AND o.user_id IS NOT NULL
      AND b.status='active'
      AND b.stock_quantity > 0
    GROUP BY o.user_id, od.book_id
    """, conn)
    conn.close()
    return df


def build_item_item_cf(df, topk=50, min_score=0.05):
    if df.empty:
        return []

    user_ids = df["user_id"].astype(int).unique()
    book_ids = df["book_id"].astype(int).unique()

    user_index = {u: i for i, u in enumerate(user_ids)}
    book_index = {b: i for i, b in enumerate(book_ids)}

    rows = df["user_id"].map(user_index).to_numpy()
    cols = df["book_id"].map(book_index).to_numpy()
    data = df["w"].astype(float).to_numpy()

    X = sparse.csr_matrix((data, (rows, cols)),
                          shape=(len(user_ids), len(book_ids)))
    item_vectors = X.T  # (num_items, num_users)

    k = min(topk + 1, item_vectors.shape[0])
    nn = NearestNeighbors(n_neighbors=k, metric="cosine",
                          algorithm="brute", n_jobs=-1)
    nn.fit(item_vectors)

    distances, indices = nn.kneighbors(item_vectors, return_distance=True)

    rows_to_insert = []
    for i, b in enumerate(book_ids):
        for dist, j in zip(distances[i], indices[i]):
            if j == i:
                continue
            score = float(1.0 - dist)
            if score < min_score:
                continue
            rows_to_insert.append(
                (int(b), int(book_ids[j]), score, "CF_PURCHASE"))
    return rows_to_insert


def save_to_db(rows):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM similar_books WHERE algo_type='CF_PURCHASE'")
    conn.commit()

    sql = """
        INSERT INTO similar_books(book_id, similar_book_id, score, algo_type)
  VALUES (%s,%s,%s,%s) AS new_rows
  ON DUPLICATE KEY UPDATE
    score = new_rows.score,
    algo_type = new_rows.algo_type
    """
    batch = 10000
    for i in range(0, len(rows), batch):
        cur.executemany(sql, rows[i:i+batch])
        conn.commit()

    cur.close()
    conn.close()


def main():
    df = load_purchase_interactions()
    print("Purchase interactions:", len(df))
    rows = build_item_item_cf(df, topk=50)
    print("Rows to insert:", len(rows))
    save_to_db(rows)
    print("Done CF_PURCHASE.")


if __name__ == "__main__":
    main()
