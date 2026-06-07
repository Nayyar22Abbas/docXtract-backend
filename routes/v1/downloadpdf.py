from fastapi.responses import FileResponse
from fastapi import APIRouter, HTTPException
import os
from bson import ObjectId
from config.db import pdfconn

#    Users can click on a PDF in the frontend and download or open it in the browser.

pdfdownload=APIRouter()

@pdfdownload.get("/download-pdf/{pdf_id}")
def download_pdf(pdf_id: str):
    """Download a PDF by its MongoDB _id."""
    doc = pdfconn.find_one({"_id": ObjectId(pdf_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="PDF not found")

    file_path = doc["saved_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing on server")

    return FileResponse(
        path=file_path,
        filename=doc["original_name"],
        media_type="application/pdf"
    )
