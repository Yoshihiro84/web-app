import json
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, RedirectResponse

from app.templating import templates
from app.services import drive_service

_BOOKMARKLET_JS_PATH = Path(__file__).resolve().parent.parent / "static" / "js" / "bookmarklet.js"

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def settings_page(request: Request):
    info = drive_service.get_settings_info()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "drive": info,
    })


@router.post("/drive")
async def settings_drive_save(
    request: Request,
    folder_id: str = Form(...),
    client_secret_file: UploadFile = File(...),
):
    content = await client_secret_file.read()
    try:
        data = json.loads(content)
        # Validate it looks like an OAuth client secret
        if not ("installed" in data or "web" in data):
            raise ValueError("Not an OAuth client secret file")
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
        info = drive_service.get_settings_info()
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "drive": info,
            "error": f"Invalid OAuth client secret JSON: {e}",
        })

    if not folder_id.strip():
        info = drive_service.get_settings_info()
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "drive": info,
            "error": "Folder ID is required",
        })

    drive_service.save_client_secret(content, folder_id)

    # Redirect to Google authorization
    auth_url = drive_service.get_auth_url()
    if not auth_url:
        info = drive_service.get_settings_info()
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "drive": info,
            "error": "Failed to generate authorization URL",
        })

    return RedirectResponse(url=auth_url, status_code=303)


@router.get("/drive/callback")
def settings_drive_callback(request: Request, code: str = "", error: str = ""):
    if error:
        info = drive_service.get_settings_info()
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "drive": info,
            "error": f"Authorization denied: {error}",
        })

    if not code:
        return RedirectResponse(url="/settings", status_code=303)

    success = drive_service.exchange_code(code)
    if success:
        return RedirectResponse(url="/settings?saved=1", status_code=303)
    else:
        info = drive_service.get_settings_info()
        return templates.TemplateResponse("settings.html", {
            "request": request,
            "drive": info,
            "error": "Failed to complete authorization. Please try again.",
        })


@router.get("/drive/authorize")
def settings_drive_authorize():
    """Re-authorize (e.g. after token expiry)."""
    auth_url = drive_service.get_auth_url()
    if not auth_url:
        return RedirectResponse(url="/settings", status_code=303)
    return RedirectResponse(url=auth_url, status_code=303)


@router.post("/drive/test")
def settings_drive_test():
    ok, message = drive_service.test_connection()
    return JSONResponse({"ok": ok, "message": message})


@router.post("/drive/disconnect")
def settings_drive_disconnect():
    drive_service.clear_settings()
    return RedirectResponse(url="/settings?disconnected=1", status_code=303)


@router.get("/bookmarklet")
def bookmarklet_page(request: Request):
    bookmarklet_js = _BOOKMARKLET_JS_PATH.read_text()
    return templates.TemplateResponse("bookmarklet.html", {
        "request": request,
        "bookmarklet_js": bookmarklet_js,
    })
