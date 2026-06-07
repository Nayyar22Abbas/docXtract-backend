from fastapi import APIRouter, HTTPException
from bson import ObjectId
from pymongo import MongoClient
from config.db import pdfconn
listpdf = APIRouter()

# MongoDB Atlas connection



@listpdf.get("/list-pdfs/{user_id}")
def list_pdfs(user_id: str):
    """Return all PDFs uploaded by a specific user."""
    pdfs = []
    for doc in pdfconn.find({"user_id": user_id}).sort("upload_time", -1):
        pdfs.append({
            "id": str(doc["_id"]),
            "original_name": doc["original_name"],
            "saved_path": doc["saved_path"],
            "upload_time": doc["upload_time"]
        })
    return {"documents": pdfs}
