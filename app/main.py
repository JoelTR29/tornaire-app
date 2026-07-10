from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, Cookie, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.database import init_db, get_connection

import json

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

@app.get("/candidat")
async def candidat(request: Request):
    return templates.TemplateResponse(request, "candidat.html", {"success": False})

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

@app.post("/empresa/nova-oferta")
async def empresa_nova_oferta(
    titol: str = Form(...),
    ubicacio: str = Form(...),
    modalitat: str = Form(...),
    salari: str = Form(...),
    correu_contacte: str = Form(...),
    descripcio: str = Form(...),
    requisits: str = Form(...),
    session_user: str = Cookie(None)  # Llegim la cookie de sessió de l'usuari connectat
):
    # 1. Verifiquem si realment hi ha una empresa connectada
    if not session_user:
        raise HTTPException(status_code=401, detail="No has iniciat sessió")
    
    user_data = json.loads(session_user)
    
    # Suposem que en fer login guardarem també el seu ID de la base de dades a la cookie.
    # Per ara, farem servir un ID temporal o el recuperarem si ja el tenim.
    user_id = user_data.get("id", 1) 

    # 2. Inserim l'oferta real a la base de dades SQLite
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO job_offers (user_id, title, location, modality, salary, contact_email, description, technical_requirements)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, titol, ubicacio, modalitat, salari, correu_contacte, descripcio, requisits))
        connection.commit()
    except Exception as e:
        connection.rollback()
        return HTMLResponse(content=f"<p class='text-red-500'>Error al desar a la base de dades: {str(e)}</p>")
    finally:
        connection.close()

    # 3. Responem amb el bloc d'èxit per a HTMX
    return HTMLResponse(content="""
        <div class="rounded-2xl border border-emerald-200 bg-emerald-50 p-6 text-emerald-900">
            <h3 class="text-xl font-bold flex items-center gap-2">🎉 Oferta Publicada i Desada a SQLite</h3>
            <p class="text-sm mt-2">L'oferta s'ha guardat amb èxit a la base de dades 'tornaire.db' vinculada al teu compte d'empresa.</p>
            <button onclick="window.location.reload()" class="mt-4 text-xs font-semibold bg-emerald-600 text-white px-4 py-2 rounded-xl hover:bg-emerald-700">Publicar una altra</button>
        </div>
    """)