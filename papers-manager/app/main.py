from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.templating import templates
from app.routes import papers, tags, collections, notes, bibtex

app = FastAPI(title="Papers Manager")

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


app.include_router(papers.router)
app.include_router(papers.api_router)
app.include_router(tags.router)
app.include_router(collections.router)
app.include_router(notes.router)
app.include_router(bibtex.router)


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
