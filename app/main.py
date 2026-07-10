from contextlib import asynccontextmanager
from pathlib import Path
import json

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, Cookie, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from app.database import init_db, get_connection
from app.auth import router as auth_router  # IMPORTAMOS TU NUEVO ARCHIVO DE AUTH

# Cargar variables del archivo .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "uploads").mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # Crea automáticamente tornaire.db con las 3 tablas nuevas
    yield

app = FastAPI(lifespan=lifespan)

# CONECTAMOS EL ROUTER DE AUTENTICACIÓN A LA APP PRINCIPAL
app.include_router(auth_router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- HELPER: Extraer datos de la cookie si existe ---
def get_current_user(session_user: str):
    if session_user:
        try:
            return json.loads(session_user)
        except Exception:
            return None
    return None

# --- VISTAS PRINCIPALES ---

@app.get("/")
async def home(request: Request, session_user: str = Cookie(None)):
    current_user = get_current_user(session_user)
    
    # 1. Connectem amb SQLite per recuperar les ofertes actives
    connection = get_connection()
    ofertes = []
    try:
        cursor = connection.cursor()
        # Fem un JOIN per obtenir el 'nom_empresa' de la taula d'usuaris usant el 'user_id'
        cursor.execute("""
            SELECT job_offers.*, users.nom_empresa 
            FROM job_offers 
            JOIN users ON job_offers.user_id = users.id 
            ORDER BY job_offers.created_at DESC
        """)
        ofertes = cursor.fetchall()  # Retorna una llista de files de la base de dades
    except Exception as e:
        print(f"⚠️ Error en carregar les ofertes: {e}")
    finally:
        connection.close()
        
    # 2. Passem la llista d'ofertes ("ofertes") cap al fitxer HTML
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "current_user": current_user,
            "ofertes": ofertes,
        },
    )

@app.get("/candidat")
async def candidat(request: Request, session_user: str = Cookie(None)):
    current_user = get_current_user(session_user)
    if not current_user or current_user.get("role") != "candidat":
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "candidat.html", {"current_user": current_user})

@app.get("/empresa")
async def empresa(request: Request, session_user: str = Cookie(None)):
    current_user = get_current_user(session_user)
    if not current_user or current_user.get("role") != "empresa":
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "empresa.html", {"current_user": current_user})


# --- ACCIONES HTMX (BASE DE DATOS REAL) ---

@app.post("/empresa/nova-oferta")
async def empresa_nova_oferta(
    titol: str = Form(...),
    ubicacio: str = Form(...),
    modalitat: str = Form(...),
    salari: str = Form(...),
    correu_contacte: str = Form(...),
    descripcio: str = Form(...),
    requisits: str = Form(...),
    session_user: str = Cookie(None)
):
    current_user = get_current_user(session_user)
    if not current_user or current_user.get("role") != "empresa":
        raise HTTPException(status_code=403, detail="Accés denegat")
        
    user_id = current_user.get("id")

    # Guardamos la oferta real en la base de datos vinculada a la empresa conectada
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
        return HTMLResponse(content=f"<div class='p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700'>Error a la DB: {str(e)}</div>")
    finally:
        connection.close()

    # Respuesta parcial HTML inyectada instantáneamente por HTMX
    return HTMLResponse(content="""
        <div class="rounded-2xl border border-emerald-200 bg-emerald-50 p-6 text-emerald-900 animate-fade-in">
            <h3 class="text-xl font-bold flex items-center gap-2">🎉 Oferta Publicada Oficialment</h3>
            <p class="text-sm mt-2">L'oferta s'ha emmagatzemat correctament a SQLite lligada al compte de la teva organització.</p>
            <button onclick="window.location.reload()" class="mt-4 text-xs font-semibold bg-emerald-600 text-white px-4 py-2 rounded-xl hover:bg-emerald-700">Publicar una altra oferta</button>
        </div>
    """)

@app.post("/candidat/enviar-manual")
async def candidat_enviar_manual(
    estudis: str = Form(...),
    experiencia: str = Form(...),
    habilitats: str = Form(...)
):
    # Aquí en la Fase 5 llamarás a Gemini pasando estos textos
    import random
    matching_percent = random.randint(65, 98)
    
    return HTMLResponse(content=f"""
        <div class="bg-white p-6 rounded-3xl border-2 border-blue-500 shadow-xl max-w-xl mx-auto text-center">
            <span class="text-4xl">📊</span>
            <h4 class="text-xl font-extrabold text-gray-900 mt-2">Resultat del Matching Automatitzat</h4>
            <div class="my-4">
                <span class="text-5xl font-black text-blue-600">{matching_percent}%</span>
                <p class="text-sm text-gray-500 mt-1">Compatibilitat estimada amb el mercat</p>
            </div>
            <p class="text-sm text-gray-600 bg-gray-50 p-4 rounded-2xl">
                <b>Anàlisi mock-up:</b> Les teves dades manuals s'han estructurat correctament en memòria per al TdR.
            </p>
        </div>
    """)

@app.post("/candidat/enviar-pdf")
async def candidat_enviar_pdf(file: UploadFile = File(...)):
    # Aquí en la Fase 3 usarás pdfplumber para leer el 'file.file'
    import random
    matching_percent = random.randint(70, 95)
    
    return HTMLResponse(content=f"""
        <div class="bg-white p-6 rounded-3xl border-2 border-emerald-500 shadow-xl max-w-xl mx-auto text-center">
            <span class="text-4xl">📄🤖</span>
            <h4 class="text-xl font-extrabold text-gray-900 mt-2">Resultat d'Anàlisi del PDF</h4>
            <div class="my-4">
                <span class="text-5xl font-black text-emerald-600">{matching_percent}%</span>
                <p class="text-sm text-gray-500 mt-1">Document processat: <b>{file.filename}</b></p>
            </div>
        </div>
    """)