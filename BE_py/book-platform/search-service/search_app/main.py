# from fastapi import FastAPI
# from app.routers.search_router import router as search_router
# from app.routers.admin_search_router import router as admin_search_router

# app = FastAPI(title="Search Service")
# app.include_router(search_router)
# app.include_router(admin_search_router)


from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from search_app.routers.search_router import router as search_router

app = FastAPI(title="Search Service")
app.include_router(search_router)

app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
