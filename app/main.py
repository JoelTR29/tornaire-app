from contextlib import asynccontextmanager
from pathlib import Path
import json

import pdfplumber

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
async def processar_pdf_candidat(request: Request, file: UploadFile = File(...), session_user: str = Cookie(None)):
    current_user = get_current_user(session_user)
    
    #  CONTROL D'ACCÉS: Si no és candidat, fora.
    if not current_user or current_user.get("role") != "candidat":
        return HTMLResponse("<div class='text-red-500 font-bold'>Error: Accés denegat.</div>", status_code=403)

    # 1. VALIDACIÓ D'EXTENSIÓ: Comprovem que sigui un PDF
    if not file.filename.lower().endswith('.pdf'):
        return HTMLResponse("""
        <div class="bg-red-50 text-red-600 p-4 rounded-xl border border-red-200 mt-4">
            <strong>⚠️ Error de format:</strong> L'arxiu pujat no és un PDF. Si us plau, puja un format vàlid (.pdf).
        </div>
        """)

    # 2. LÒGICA DE LECTURA (pdfplumber)
    text_cv = ""
    try:
        # Obrim l'arxiu temporal directament des de la memòria de FastAPI
        with pdfplumber.open(file.file) as pdf:
            # Fem un bucle per totes les pàgines (per si el CV en té més d'una)
            for page in pdf.pages:
                text_extret = page.extract_text()
                if text_extret:
                    text_cv += text_extret + "\n"
                    
    except Exception as e:
        return HTMLResponse(f"""
        <div class="bg-red-50 text-red-600 p-4 rounded-xl border border-red-200 mt-4">
            <strong>🚨 Error de lectura:</strong> No s'ha pogut obrir el PDF. Podria estar corrupte o protegit amb contrasenya. 
            <span class="text-xs block mt-1">Detall: {e}</span>
        </div>
        """)

    # 3. VALIDACIÓ DE CONTINGUT: Evitem PDFs escanejats (imatges sense text)
    if not text_cv.strip():
        return HTMLResponse("""
        <div class="bg-orange-50 text-orange-700 p-4 rounded-xl border border-orange-200 mt-4">
            <strong>👀 Avís important:</strong> No s'ha trobat text al document. Assegura't que el PDF conté text digital i no és una imatge escanejada o una fotografia.
        </div>
        """)

    # 4. PONT CAP A LA FASE 4/5: Mostrem un avís visual a l'usuari amb el resultat de l'extracció
    # Més endavant, aquest text_cv s'enviarà a l'API de Gemini abans de retornar res.
    return HTMLResponse(f"""
    <div class="bg-emerald-50 text-emerald-800 p-6 rounded-2xl border border-emerald-200 mt-6 shadow-sm">
        <h3 class="font-bold text-lg mb-2 flex items-center gap-2">
            <span>📄</span> Extracció de text completada amb èxit!
        </h3>
        <p class="mb-4 text-sm">
            Hem extret <strong>{len(text_cv)} caràcters</strong> del teu document. Això és el que la IA llegirà:
        </p>
        
        <!-- Previsualització del text extret -->
        <div class="bg-white p-4 rounded-xl border border-emerald-100 text-sm text-gray-600 max-h-40 overflow-y-auto mb-4 shadow-inner">
            <p class="font-mono text-xs whitespace-pre-wrap">{text_cv[:400]}...</p>
        </div>
        
        <p class="text-xs font-semibold text-emerald-600">
            ✅ Llest per connectar amb l'API de Gemini (Fase 4).
        </p>
    </div>
    """)