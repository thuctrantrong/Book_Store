# ------------------------------------------------------------
# File này xử lý cập nhật mô hình Content-Based TF-IDF theo kiểu *incremental*.
# ------------------------------------------------------------
# Nghĩa là chúng ta KHÔNG bao giờ build lại toàn bộ TF-IDF matrix (rất nặng).
# Thay vào đó:
#
# ✔ Khi THÊM sách mới:
#     - Vectorizer đã được fit trước → dùng lại
#     - Tạo vector TF-IDF cho sách mới
#     - Tính similarity giữa sách mới ↔ toàn bộ sách hiện có
#     - Cập nhật top-k similarity cho sách mới
#     - Cập nhật top-k của các sách khác nếu sách mới ảnh hưởng
#     - Append vector mới vào tfidf_matrix (không rebuild)
#
# ✔ Khi XÓA sách:
#     - Chỉ xóa khỏi bảng similar_books
#     - Remove khỏi mapping book_index
#     - Không xóa row trong matrix (tránh phải reindex toàn bộ)
#     - Đánh dấu "deleted_ids" → rebuild định kỳ sẽ dọn sạch
#
# ✔ Khi CẬP NHẬT sách:
#     - Tính lại vector TF-IDF của sách đó
#     - Thay thế trực tiếp row trong tfidf_matrix
#     - Tính lại similarity cho cuốn đó
#
# Mục đích: cập nhật nhanh theo thời gian thực (real-time)
# mà không tốn CPU/RAM như rebuild toàn bộ matrix.
# ------------------------------------------------------------


# app/services/content_based/incremental.py
"""
Incremental TF-IDF updater for content-based recommender.

Usage (CLI):
  python incremental.py add <book_id>
  python incremental.py update <book_id>
  python incremental.py delete <book_id>

Functions:
  incremental_add_book(book_id, top_k=20)
  incremental_update_book(book_id, top_k=20)
  incremental_delete_book(book_id)
"""
import os
import sys
import json
import pickle
import tempfile
import argparse
import time
import numpy as np
import pandas as pd
from scipy import sparse

# If build_cb_tfidf is in same package, import helpers; otherwise copy-normalizer from there.
try:
    # adjust import if your build_cb_tfidf.py is in the same folder
    from .build_cb_tfidf import norm_token, year_bucket  # relative import
except Exception:
    try:
        from build_cb_tfidf import norm_token, year_bucket  # fallback
    except Exception:
        # minimal fallback (not ideal but safe)
        import re

        def norm_token(x: str) -> str:
            x = (x or "").strip().lower()
            x = re.sub(r"\s+", "_", x)
            x = re.sub(r"[^0-9a-zA-Z_À-ỹ]", "", x)
            return x

        def year_bucket(y):
            try:
                y = int(y)
                return f"{(y//10)*10}s"
            except:
                return ""

# DB connection helper (you must have app.db.get_connection available)
try:
    from recommend_app.db import get_connection
except Exception:
    # fallback: try local import
    from db import get_connection  # if you have db.py at project root
    # if not present, get_connection must be provided by you

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model_data")
VECTOR_PATH = os.path.join(MODEL_DIR, "vectorizer.pkl")
MATRIX_PATH = os.path.join(MODEL_DIR, "tfidf_matrix.npz")
BOOK_IDS_CSV = os.path.join(MODEL_DIR, "book_ids.csv")
META_PATH = os.path.join(MODEL_DIR, "meta.json")

TOP_K_DEFAULT = 20
LOCK_NAME = "cb_incremental_lock"
LOCK_TIMEOUT = 10  # seconds to wait for lock

os.makedirs(MODEL_DIR, exist_ok=True)


# ---------------------------
# Model load / save
# ---------------------------
def load_model():
    """Load vectorizer, tfidf_matrix and book_ids list.
    Returns: vectorizer, tfidf_matrix (csr), book_ids(list of ints)
    """
    if not os.path.exists(VECTOR_PATH):
        raise RuntimeError(
            f"Vectorizer not found at {VECTOR_PATH}. Run full build first.")
    with open(VECTOR_PATH, "rb") as f:
        vectorizer = pickle.load(f)

    # If matrix not present, return empty matrix
    if os.path.exists(MATRIX_PATH):
        tfidf_matrix = sparse.load_npz(MATRIX_PATH)
    else:
        tfidf_matrix = sparse.csr_matrix(
            (0, vectorizer.max_features if hasattr(vectorizer, "max_features") else 0))

    # load book ids order
    if os.path.exists(BOOK_IDS_CSV):
        df = pd.read_csv(BOOK_IDS_CSV)
        book_ids = [int(x) for x in df["book_id"].tolist()]
    else:
        book_ids = []

    return vectorizer, tfidf_matrix, book_ids


def save_model(tfidf_matrix, book_ids, meta=None):
    """Atomically save tfidf_matrix (.npz) and book_ids.csv and meta.json (optional)."""
    os.makedirs(MODEL_DIR, exist_ok=True)

    # save matrix atomically
    tmpm = MATRIX_PATH + ".tmp"
    sparse.save_npz(tmpm, tfidf_matrix)
    os.replace(tmpm, MATRIX_PATH)

    # save book_ids
    tmpb = BOOK_IDS_CSV + ".tmp"
    pd.DataFrame({"book_id": list(map(int, book_ids))}
                 ).to_csv(tmpb, index=False)
    os.replace(tmpb, BOOK_IDS_CSV)

    if meta is not None:
        tmpj = META_PATH + ".tmp"
        with open(tmpj, "w", encoding="utf8") as f:
            json.dump(meta, f, ensure_ascii=False)
        os.replace(tmpj, META_PATH)


# ---------------------------
# Helpers: text compose & DB fetch/write
# ---------------------------
def make_full_text(row: dict) -> str:
    """Compose full_text using same weighting as full build."""
    title = (row.get("title") or "") + " "
    categories = (row.get("categories") or "") + " "
    author_name = (row.get("author_name") or "") + " "
    pub_tok = f"pub_{norm_token(row.get('publisher_name'))}" if row.get(
        "publisher_name") else ""
    fmt_tok = f"fmt_{norm_token(row.get('format'))}" if row.get(
        "format") else ""
    lang_tok = f"lang_{norm_token(row.get('language'))}" if row.get(
        "language") else ""
    year_tok = f"year_{year_bucket(row.get('publication_year'))}" if row.get(
        "publication_year") else ""
    desc = row.get("description") or ""
    full = (title * 4) + (categories * 2) + (author_name * 2) + (pub_tok + " ") * \
        2 + (fmt_tok + " ") * 2 + (lang_tok + " ") + (year_tok + " ") + desc
    return full


def fetch_book_row(book_id: int):
    """Fetch metadata for a book from DB."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    sql = """
    SELECT 
        b.book_id, b.title, b.description, a.author_name, p.publisher_name, b.format, b.language, b.publication_year,
        GROUP_CONCAT(DISTINCT c.category_name ORDER BY c.category_name SEPARATOR ' ') AS categories
    FROM books b
    LEFT JOIN authors a ON b.author_id = a.author_id
    LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
    LEFT JOIN book_categories bc ON bc.book_id = b.book_id
    LEFT JOIN categories c ON c.category_id = bc.category_id
    WHERE b.book_id = %s
    GROUP BY b.book_id, b.title, b.description, a.author_name, p.publisher_name, b.format, b.language, b.publication_year
    """
    cur.execute(sql, (book_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def write_similar_rows_to_db(book_id: int, sim_ids_scores):
    """
    Replace top-K similar rows for book_id with sim_ids_scores list[(similar_book_id, score)].
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM similar_books WHERE book_id = %s AND algo_type = 'TFIDF'", (book_id,))
    if sim_ids_scores:
        sql = "INSERT INTO similar_books (book_id, similar_book_id, score, algo_type) VALUES (%s,%s,%s,'TFIDF')"
        data = [(book_id, int(sid), float(score))
                for sid, score in sim_ids_scores]
        cur.executemany(sql, data)
    conn.commit()
    cur.close()
    conn.close()


# ---------------------------
# Lock helpers (MySQL GET_LOCK)
# ---------------------------
def acquire_lock(conn, lock_name=LOCK_NAME, timeout=LOCK_TIMEOUT) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT GET_LOCK(%s, %s)", (lock_name, timeout))
    res = cur.fetchone()
    cur.close()
    return bool(res and res[0] == 1)


def release_lock(conn, lock_name=LOCK_NAME):
    cur = conn.cursor()
    try:
        cur.execute("SELECT RELEASE_LOCK(%s)", (lock_name,))
    finally:
        cur.close()


# ---------------------------
# Incremental operations
# ---------------------------
def incremental_add_book(book_id: int, top_k: int = TOP_K_DEFAULT):
    """Add a new book to model_data and compute+store its top-k similar books."""
    started = time.time()
    conn = get_connection()
    try:
        if not acquire_lock(conn):
            raise RuntimeError("Could not acquire incremental lock")

        # load model
        vectorizer, tfidf_matrix, book_ids = load_model()

        # fetch book
        row = fetch_book_row(book_id)
        if not row:
            raise ValueError(f"Book {book_id} not found in DB")

        # compose full text and transform
        full_text = make_full_text(row)
        vec_new = vectorizer.transform([full_text])  # shape (1, d)

        # compute similarities against existing matrix (before appending)
        if tfidf_matrix.shape[0] > 0:
            sims = vec_new.dot(tfidf_matrix.T).A1  # (n_existing,)
        else:
            sims = np.array([])

        # choose top-k indices among existing books
        if sims.size:
            k = min(top_k, sims.size)
            top_idx = np.argpartition(sims, -k)[-k:]
            top_idx = top_idx[np.argsort(sims[top_idx])[::-1]]
            sim_pairs = [(book_ids[int(i)], float(sims[int(i)]))
                         for i in top_idx]
        else:
            sim_pairs = []

        # write top-k for the new book
        write_similar_rows_to_db(book_id, sim_pairs)

        # Append vector to tfidf_matrix and append id to book_ids
        vec_new_csr = sparse.csr_matrix(vec_new)
        if tfidf_matrix.shape[0] == 0:
            new_matrix = vec_new_csr
        else:
            # stack existing + new
            new_matrix = sparse.vstack(
                [tfidf_matrix, vec_new_csr], format="csr")

        book_ids.append(int(book_id))

        # save updated matrix and book_ids (do not rewrite vectorizer)
        meta = {"last_incremental_add": int(
            book_id), "n_books": new_matrix.shape[0], "ts": time.time()}
        save_model(new_matrix, book_ids, meta=meta)

        elapsed = time.time() - started
        print(
            f"[incremental_add_book] done book={book_id} topk={len(sim_pairs)} time={elapsed:.2f}s")
        return True

    finally:
        try:
            release_lock(conn)
        except Exception:
            pass
        conn.close()


def incremental_update_book(book_id: int, top_k: int = TOP_K_DEFAULT):
    """Update an existing book: recompute vector and new top-k for that book."""
    started = time.time()
    conn = get_connection()
    try:
        if not acquire_lock(conn):
            raise RuntimeError("Could not acquire incremental lock")

        vectorizer, tfidf_matrix, book_ids = load_model()

        if int(book_id) not in map(int, book_ids):
            # if not present, treat as add
            print(
                f"[incremental_update_book] book_id {book_id} not in book_ids -> call add")
            return incremental_add_book(book_id, top_k=top_k)

        idx = book_ids.index(int(book_id))

        # fetch and compute
        row = fetch_book_row(book_id)
        if not row:
            raise ValueError(f"Book {book_id} not found in DB")
        full_text = make_full_text(row)
        vec_new = vectorizer.transform([full_text])  # (1,d)

        # replace row in matrix (convert to lil for assign)
        tfidf_lil = tfidf_matrix.tolil()
        tfidf_lil[idx, :] = vec_new
        tfidf_matrix_new = tfidf_lil.tocsr()

        # compute sims (book vs all)
        sims = tfidf_matrix_new[idx].dot(tfidf_matrix_new.T).A1
        sims[idx] = -1.0

        # top-k
        k = min(top_k, len(sims) - 1) if len(sims) > 1 else 0
        if k > 0:
            top_idx = np.argpartition(sims, -k)[-k:]
            top_idx = top_idx[np.argsort(sims[top_idx])[::-1]]
            sim_pairs = [(book_ids[int(i)], float(sims[int(i)]))
                         for i in top_idx]
        else:
            sim_pairs = []

        # write new top-k for this book
        write_similar_rows_to_db(book_id, sim_pairs)

        # optionally, one could update other books' lists as well (skipped for speed/complexity)

        # save updated matrix
        meta = {"last_incremental_update": int(
            book_id), "n_books": tfidf_matrix_new.shape[0], "ts": time.time()}
        save_model(tfidf_matrix_new, book_ids, meta=meta)

        elapsed = time.time() - started
        print(
            f"[incremental_update_book] done book={book_id} topk={len(sim_pairs)} time={elapsed:.2f}s")
        return True

    finally:
        try:
            release_lock(conn)
        except Exception:
            pass
        conn.close()


def incremental_delete_book(book_id: int):
    """Delete book from similar_books and remove from book_ids (hard remove).
    Note: This physically removes row from tfidf_matrix and reindexes subsequent rows.
    This is OK for moderate dataset sizes; for extremely large datasets you may prefer soft-delete.
    """
    started = time.time()
    conn = get_connection()
    try:
        if not acquire_lock(conn):
            raise RuntimeError("Could not acquire incremental lock")

        vectorizer, tfidf_matrix, book_ids = load_model()
        book_id = int(book_id)
        if book_id not in book_ids:
            # nothing to do
            print(f"[incremental_delete_book] book {book_id} not in model")
        else:
            idx = book_ids.index(book_id)

            # Delete similar_books rows in DB referencing this book
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM similar_books WHERE book_id = %s OR similar_book_id = %s", (book_id, book_id))
            conn.commit()
            cur.close()

            # remove row from matrix
            n_rows = tfidf_matrix.shape[0]
            if n_rows <= 1:
                new_matrix = sparse.csr_matrix((0, tfidf_matrix.shape[1]))
            else:
                mask = np.ones(n_rows, dtype=bool)
                mask[idx] = False
                new_matrix = tfidf_matrix[mask]

            # remove id from list
            book_ids.pop(idx)

            # save model
            meta = {"last_incremental_delete": int(
                book_id), "n_books": new_matrix.shape[0], "ts": time.time()}
            save_model(new_matrix, book_ids, meta=meta)

            print(
                f"[incremental_delete_book] removed book={book_id} idx={idx}")

        elapsed = time.time() - started
        print(
            f"[incremental_delete_book] done book={book_id} time={elapsed:.2f}s")
        return True

    finally:
        try:
            release_lock(conn)
        except Exception:
            pass
        conn.close()


# ---------------------------
# CLI support
# ---------------------------
def _cli():
    p = argparse.ArgumentParser(description="Incremental TF-IDF manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("add")
    pa.add_argument("book_id", type=int)

    pu = sub.add_parser("update")
    pu.add_argument("book_id", type=int)

    pd = sub.add_parser("delete")
    pd.add_argument("book_id", type=int)

    p.add_argument("--topk", type=int, default=TOP_K_DEFAULT)

    args = p.parse_args()

    if args.cmd == "add":
        incremental_add_book(args.book_id, top_k=args.topk)
    elif args.cmd == "update":
        incremental_update_book(args.book_id, top_k=args.topk)
    elif args.cmd == "delete":
        incremental_delete_book(args.book_id)
    else:
        p.print_help()


if __name__ == "__main__":
    _cli()
