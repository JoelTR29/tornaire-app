from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db

# Cargar variables del archivo .env
load_dotenv()

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carpetas del proyecto
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Crear carpetas si no existen
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "uploads").mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Se ejecuta al arrancar FastAPI.
    Crea automáticamente la base de datos tornaire.db
    y las tablas necesarias si todavía no existen.
    """
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# Configurar carpetas estáticas y plantillas HTML
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        name="index.html",
        request=request,
        context={}
    )

@app.get("/empresa")
async def empresa(request: Request):
    return templates.TemplateResponse(request, "empresa.html", {"success": False})


@app.post("/empresa")
async def empresa_submit(
    request: Request,
    titulo: str = Form(...),
    ubicacion: str = Form(...),
    modalidad: str = Form(...),
    salario: str = Form(...),
    descripcion: str = Form(...),
    requisitos: str = Form(...),
    contacto: str = Form(...),
):
    oferta = {
        "titulo": titulo,
        "ubicacion": ubicacion,
        "modalidad": modalidad,
        "salario": salario,
        "descripcion": descripcion,
        "requisitos": requisitos,
        "contacto": contacto,
    }
    return templates.TemplateResponse(
        request,
        "empresa.html",
        {"success": True, "oferta": oferta},
    )