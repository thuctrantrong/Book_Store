import re
import os
import mysql.connector
import pandas as pd
from dotenv import load_dotenv
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from scipy import sparse
import pickle


def save_tfidf_model(df_books, vectorizer, tfidf_matrix):
    os.makedirs("model_data", exist_ok=True)

    # save vectorizer
    with open("model_data/vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)

    # save tfidf matrix
    sparse.save_npz("model_data/tfidf_matrix.npz", tfidf_matrix)

    # save book_id order
    df_books[["book_id"]].to_csv("model_data/book_ids.csv", index=False)

    print("Saved TF-IDF model files in model_data/")


# =========================
# 1. Load config & connect DB
# =========================
load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DB = os.getenv("MYSQL_DB", "bookstore")


def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
    )


# =========================
# 2. Load dữ liệu sách
# =========================
def load_books():
    conn = get_connection()
    query = """
        SELECT 
            b.book_id,
            b.title,
            b.description,
            a.author_name,
            p.publisher_name,
            b.format,
            b.language,
            b.publication_year,
            GROUP_CONCAT(DISTINCT c.category_name ORDER BY c.category_name SEPARATOR ' ') AS categories
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.author_id
        LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
        LEFT JOIN book_categories bc ON bc.book_id = b.book_id
        LEFT JOIN categories c ON c.category_id = bc.category_id
        WHERE b.status = 'active'
        AND b.stock_quantity > 0
        GROUP BY b.book_id, b.title, b.description, a.author_name, p.publisher_name, b.format, b.language, b.publication_year
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


# =========================
# 3. Build full_text & TF-IDF
# =========================


def norm_token(x: str) -> str:
    x = (x or "").strip().lower()
    x = re.sub(r"\s+", "_", x)
    x = re.sub(r"[^0-9a-zA-Z_À-ỹ]", "", x)  # giữ unicode tiếng Việt cơ bản
    return x


def year_bucket(y):
    try:
        y = int(y)
        return f"{(y//10)*10}s"   # 2024 -> 2020s
    except:
        return ""


def build_tfidf(df_books: pd.DataFrame):
    for col in ["title", "description", "author_name", "categories", "publisher_name", "format", "language", "publication_year"]:
        df_books[col] = df_books[col].fillna("")

    df_books["fmt_tok"] = df_books["format"].apply(
        lambda x: f"fmt_{norm_token(x)}" if x else "")
    df_books["lang_tok"] = df_books["language"].apply(
        lambda x: f"lang_{norm_token(x)}" if x else "")
    df_books["pub_tok"] = df_books["publisher_name"].apply(
        lambda x: f"pub_{norm_token(x)}" if x else "")
    df_books["year_tok"] = df_books["publication_year"].apply(
        lambda x: f"year_{year_bucket(x)}" if x else "")

    # weight: title mạnh nhất, category/publisher/format khá mạnh, author vừa, desc nhẹ hơn
    df_books["full_text"] = (
        (df_books["title"] + " ") * 4 +
        (df_books["categories"] + " ") * 2 +
        (df_books["author_name"] + " ") * 2 +
        (df_books["pub_tok"] + " ") * 2 +
        (df_books["fmt_tok"] + " ") * 2 +
        (df_books["lang_tok"] + " ") * 1 +
        (df_books["year_tok"] + " ") * 1 +
        df_books["description"]
    )

    vectorizer = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b\w+\b",
        min_df=2,
    )
    tfidf_matrix = vectorizer.fit_transform(df_books["full_text"])
    return df_books, vectorizer, tfidf_matrix


# =========================
# 4. Tính similarity & chuẩn bị dữ liệu insert
# =========================

def build_similar_rows(df_books: pd.DataFrame, tfidf_matrix, n_similar: int = 50):
    book_ids = df_books["book_id"].astype(int).values
    n = len(book_ids)
    n_similar = min(n_similar, n - 1)

    rows_to_insert = []

    # tfidf_matrix: (n, d) sparse
    for i, book_id in enumerate(book_ids):
        sims = tfidf_matrix[i].dot(tfidf_matrix.T).toarray()[0]
        sims[i] = -1  # loại chính nó

        # lấy top-k nhanh
        topk_idx = np.argpartition(sims, -n_similar)[-n_similar:]
        topk_idx = topk_idx[np.argsort(sims[topk_idx])[::-1]]

        for j in topk_idx:
            rows_to_insert.append(
                (int(book_id), int(book_ids[j]), float(sims[j]), "TFIDF"))

    return rows_to_insert


# =========================
# 5. Ghi vào bảng similar_books
# =========================
def save_similar_to_db(rows_to_insert):
    conn = get_connection()
    cursor = conn.cursor()

    # Xóa dữ liệu cũ của TFIDF
    cursor.execute("DELETE FROM similar_books WHERE algo_type = 'TFIDF'")
    conn.commit()

    sql = """
    INSERT INTO similar_books (book_id, similar_book_id, score, algo_type)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE score=VALUES(score), algo_type=VALUES(algo_type)
    """

    batch_size = 10000
    for i in range(0, len(rows_to_insert), batch_size):
        cursor.executemany(sql, rows_to_insert[i:i+batch_size])
        conn.commit()

    conn.commit()

    cursor.close()
    conn.close()


# =========================
# 6. Main
# =========================
def main():
    print("Loading books...")
    df_books = load_books()
    print("Num books:", len(df_books))

    if df_books.empty:
        print("No books found. Exit.")
        return

    print("Building TF-IDF...")
    df_books, vectorizer, tfidf_matrix = build_tfidf(df_books)

    print("Computing similarities...")
    rows_to_insert = build_similar_rows(df_books, tfidf_matrix, n_similar=50)
    print("Total rows to insert:", len(rows_to_insert))

    print("Saving to DB...")
    save_similar_to_db(rows_to_insert)

    save_tfidf_model(df_books, vectorizer, tfidf_matrix)

    print("Done.")


if __name__ == "__main__":
    main()
