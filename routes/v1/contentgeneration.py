from fastapi import APIRouter,Request,Form
import markdown
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse,JSONResponse
from Services.googlevertexai import contentcreation
from pydantic import BaseModel
# from Services.iamge_generation import generate_image


router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/userprompt")
def get_users(request:Request):

    return templates.TemplateResponse("/prompt_form.html", {"request":request})







@router.post("/userprompt")
def post_user(prompt: str=Form(...)):
    generatedresult=contentcreation(prompt)
    cleanedresponse=generatedresult.replace("\\n","\n").replace("\\","")
    formattedresponse=markdown.markdown(cleanedresponse)


   
    return JSONResponse(content={"response":formattedresponse})







#    FOR POST MAN TESTING AND RETURNING JSON SO THAT POSTMAN CAN UNDERSTAND

# class PromptRequest(BaseModel):
#     prompt: str

# @router.post("/userprompt")
# def post_user_json(data: PromptRequest):
#     generatedresult = contentcreation(data.prompt)
#     cleanedresponse = generatedresult.replace("\\n", "\n").replace("\\", "")
#     formattedresponse = markdown.markdown(cleanedresponse)

#     # Return JSON that Postman can process
#     return {"prompt": formattedresponse}





# image generation API's



# @router.get("/generate-image", response_class=HTMLResponse)
# async def image_form(request: Request):
#     return templates.TemplateResponse("image_form.html", {"request": request})

# @router.post("/generate-image", response_class=HTMLResponse)
# async def create_image(request: Request, prompt: str = Form(...)):
#     image_url = generate_image(prompt)
#     return templates.TemplateResponse("image_form.html", {
#         "request": request,
#         "image_url": image_url
#     })

