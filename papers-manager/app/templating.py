from pathlib import Path
from fastapi.templating import Jinja2Templates
from app.services.markdown_service import render_markdown

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
templates.env.filters["markdown"] = render_markdown
