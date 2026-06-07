from fastapi import APIRouter
from config.db import pdfconn
from fastapi import HTTPException
from bson import ObjectId




deletepdf=APIRouter()

@deletepdf.delete("/pdf/{pdf_id}")
def delete_pdf(pdf_id: str):
    try:
        file_id = ObjectId(pdf_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid PDF ID")

    result = pdfconn.delete_one({"_id": file_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="PDF not found")

    return {"message": "PDF deleted successfully", "pdf_id": pdf_id}
