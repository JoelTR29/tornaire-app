from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

# Cargar las variables del .env
load_dotenv()

app = FastAPI()

# Configurar carpetas estáticas y plantillas HTML
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    # Esto renderizará un index.html (que crearás luego) basándose en base.html
    return templates.TemplateResponse("index.html", {"request": request})