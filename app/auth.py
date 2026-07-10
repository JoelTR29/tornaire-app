# app/auth.py
import json
import sqlite3
from pathlib import Path
from fastapi import APIRouter, Request, Form, Response, Cookie
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database import get_connection

# Creamos un Router independiente para la autenticación
router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"current_user": None})

@router.post("/login")
async def login_submit(
    request: Request,
    role: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        # Buscamos al usuario por su correo electrónico
        cursor.execute(
            "SELECT id, role, nom, nom_empresa, email, password FROM users WHERE email = ?", 
            (email,)
        )
        user = cursor.fetchone()
        
        # Validación 1: ¿Existe el email?
        if not user:
            return templates.TemplateResponse(request, "login.html", {
                "error": "El correu electrònic no està registrat.", 
                "current_user": None
            })
        
        # Validación 2: ¿La contraseña coincide? (Para el MVP local la comparamos directamente)
        if user["password"] != password:
            return templates.TemplateResponse(request, "login.html", {
                "error": "Contrasenya incorrecta.", 
                "current_user": None
            })
        
        # Validación 3: ¿El rol seleccionado coincide con el de la base de datos?
        if user["role"] != role:
            return templates.TemplateResponse(request, "login.html", {
                "error": f"Aquest compte no està registrat com a {role}.", 
                "current_user": None
            })
        
        # Si todo es correcto, preparamos los datos que guardaremos en la Cookie
        user_data = {
            "id": user["id"],
            "role": user["role"],
            "nom": user["nom"],
            "nom_empresa": user["nom_empresa"],
            "email": user["email"]
        }
        
        # Redirigimos según el tipo de usuario
        target_url = "/empresa" if role == "empresa" else "/candidat"
        response = RedirectResponse(url=target_url, status_code=303)
        
        # Guardamos la sesión en el navegador (caduca al cerrar el navegador)
        response.set_cookie(key="session_user", value=json.dumps(user_data), path="/")
        return response
        
    finally:
        connection.close()

@router.get("/registre")
async def registre_page(request: Request):
    return templates.TemplateResponse(request, "registre.html", {"current_user": None})

@router.post("/registre")
async def registre_submit(
    request: Request,
    role: str = Form(...),
    nom: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    nom_empresa: str = Form(None)
):
    # Validación: Si es empresa, obligar a poner el nombre comercial
    if role == "empresa" and not nom_empresa:
        return templates.TemplateResponse(request, "registre.html", {
            "error": "El nom de l'empresa és obligatori per a perfils d'empresa."
        })
        
    connection = get_connection()
    try:
        cursor = connection.cursor()
        # Insertamos el nuevo usuario de forma segura con consultas parametrizadas (evita SQL Injection)
        cursor.execute(
            "INSERT INTO users (role, nom, nom_empresa, email, password) VALUES (?, ?, ?, ?, ?)",
            (role, nom, nom_empresa if role == "empresa" else None, email, password)
        )
        connection.commit()
        
        # Registro completado con éxito -> Vamos al login
        return RedirectResponse(url="/login", status_code=303)
        
    except sqlite3.IntegrityError:
        # Esto salta automáticamente gracias al 'UNIQUE' que pusimos en el modelo del email
        return templates.TemplateResponse(request, "registre.html", {
            "error": "Aquest correu electrònic ja està registrat en el sistema."
        })
    finally:
        connection.close()

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_user", path="/")  # Borramos la cookie de sesión
    return response