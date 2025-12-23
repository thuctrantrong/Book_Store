from fastapi import APIRouter
from search_app.search.indexer import index_one_book

router = APIRouter(prefix="/admin/search", tags=["AdminSearch"])


@router.post("/index-book/{book_id}")
def index_book(book_id: int):
    return index_one_book(book_id)
