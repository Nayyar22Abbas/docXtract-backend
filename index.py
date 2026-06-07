from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from routes.v1.contentgeneration import router
from routes.v1.userauth import authuser
from routes.v1.protectedroute import protected_router
from routes.v1.pdf_summary_combined import pdf_summary_combined
from routes.v1.downloadpdf import pdfdownload
from routes.v1.chatwithpdf import pdfchat
from routes.v1.showlistpdf import listpdf
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from routes.v1.deletepdf import deletepdf
from routes.v1.pdfcomparison import pdfcompare
from routes.v1.lit_review_builder import lit_review_router
from routes.v1.quiz import quiz_router

from routes.v2.pdf_chat_model import modelpdfchat

from routes.v2.pdf_summary_model import pdfsummarymodel

from routes.v2.flashcard import flashcard
from routes.v2.flashcard_citation import flashcardWithcitation 



from routes.v2.mcqs import mcqs
from routes.v2.quiz_model import quiz_model_router
from routes.v2.insight_generation import insight_router
import os




 
app= FastAPI()


origins=[
    "http://localhost:3000",  
    "http://localhost",
    "http://127.0.0.1:3000",
    "https://doc-xtract-frontend.vercel.app/",
    "https://doc-xtract-frontend.vercel.app",
    FRONTEND_URL
  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],       #allow all HTTP methods
    allow_headers=["*"]        #allow all headers
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET","supersecret")   


)
#version 1 with gemini API
app.include_router(router,prefix="/users", tags=["Users"])
app.include_router(authuser,prefix="/authuser",tags=["AuthUser"])
app.include_router(protected_router,prefix="/protected_route", tags=["protected"])
app.include_router(pdf_summary_combined,prefix="/summary", tags=["Summary"])
app.include_router(pdfdownload,prefix="/pdfdownload", tags=["pdf"])
app.include_router(listpdf,prefix="/list", tags=["pdf"])
app.include_router(pdfchat,prefix="/pdfchat", tags=["pdf"])
app.include_router(deletepdf,prefix="/deletepdf", tags=["pdf"])
app.include_router(pdfcompare,prefix="/ppdfcomparison", tags=["pdf comparison"])
app.include_router(lit_review_router,prefix="/lit-review", tags=["Literature Review"])
app.include_router(quiz_router,prefix="/v1/quiz", tags=["Quiz"])

#version 2 with model implementation

app.include_router(modelpdfchat,prefix="/modelpdfchat", tags=["model"])

app.include_router(pdfsummarymodel,prefix="/modelpdfsummary", tags=["model"])
app.include_router(quiz_model_router,prefix="/v2/quiz", tags=["model"])


app.include_router(mcqs,prefix="/mcqgeneration", tags=["model"])
app.include_router(flashcard,prefix="/flashcard", tags=["model"])
app.include_router(flashcardWithcitation,prefix="/flashcardwithcitation", tags=["model"])
app.include_router(insight_router, prefix="/insight/v2", tags=["insight"])

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


