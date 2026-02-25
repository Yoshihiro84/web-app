from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import Response, JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Paper
from app.services import drive_service

router = APIRouter(prefix="/api/papers", tags=["pdf"])


@router.post("/{paper_id}/pdf")
async def upload_pdf(
    paper_id: int,
    pdf_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if not drive_service.is_configured():
        raise HTTPException(status_code=503, detail="Google Drive is not configured")

    if not (pdf_file.filename or "").lower().endswith(".pdf") and pdf_file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    file_bytes = await pdf_file.read()
    filename = f"paper_{paper_id}_{pdf_file.filename}"

    # Delete old PDF if exists
    if paper.pdf_drive_file_id:
        drive_service.delete_pdf(paper.pdf_drive_file_id)

    try:
        file_id = drive_service.upload_pdf(file_bytes, filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drive upload error: {e}")
    if not file_id:
        raise HTTPException(status_code=500, detail="Failed to upload PDF to Drive")

    paper.pdf_drive_file_id = file_id
    db.commit()

    return JSONResponse({"pdf_drive_file_id": file_id})


@router.get("/{paper_id}/pdf")
def get_pdf(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if not paper.pdf_drive_file_id:
        raise HTTPException(status_code=404, detail="No PDF attached")

    pdf_bytes = drive_service.download_pdf(paper.pdf_drive_file_id)
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="Failed to download PDF from Drive")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=paper_{paper_id}.pdf"},
    )


@router.delete("/{paper_id}/pdf")
def delete_pdf(paper_id: int, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    if not paper.pdf_drive_file_id:
        raise HTTPException(status_code=404, detail="No PDF attached")

    drive_service.delete_pdf(paper.pdf_drive_file_id)
    paper.pdf_drive_file_id = None
    db.commit()

    return JSONResponse({"status": "deleted"})
