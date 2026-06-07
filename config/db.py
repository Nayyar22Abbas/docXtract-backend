from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Try to use environment variable, fallback to hardcoded URI
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://AhsanAli:221849123@mycluster.tgkmqdz.mongodb.net/DOCxTRACT")

try:
    conn = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Try to connect to verify it works
    conn.admin.command('ping')
    print("✅ Connected to MongoDB successfully")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {str(e)}")
    print("⚠️  Make sure:")
    print("   1. MongoDB Atlas cluster is running")
    print("   2. Your IP is whitelisted in MongoDB Atlas")
    print("   3. Your internet connection is working")
    print("   4. The MongoDB URI is correct")
    # Exit so the error is clear
    raise

authconn = conn.DOCxTRACT.users
pdfconn = conn.DOCxTRACT.pdf_files
quizconn = conn.DOCxTRACT.quizzes

# later motor will be used to support the async operations
# async_conn=AsyncIOMotorClient(MONGO_URI)
# authconn=async_conn.DOCxTRACT.users





