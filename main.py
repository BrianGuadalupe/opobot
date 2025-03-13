from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from supabase import create_client
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

# Variables de entorno
api_key = os.getenv("SAMBANOVA_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Clientes externos
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(base_url="https://api.sambanova.ai/v1/", api_key=api_key)

# Inicializa aplicación FastAPI
app = FastAPI()

# Configuración CORS (seguridad del frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint principal (sirve frontend)
@app.get("/")
def index():
    return FileResponse("frontend/index.html")

# Endpoint para interacción con IA (SambaNova)
@app.post("/pregunta")
async def pregunta(datos: dict):
    try:
        pregunta_usuario = datos["pregunta"]
        completion = client.chat.completions.create(
            model="Meta-Llama-3.1-405B-Instruct",
            messages=[{"role": "user", "content": pregunta_usuario}],
        )
        respuesta = completion.choices[0].message.content
        return {"respuesta": respuesta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para registrar academias en Supabase
@app.post("/registrar_academia")
async def registrar_academia(datos: dict):
    nombre = datos['nombre']
    email = datos['email']
    contraseña_plana = datos['contraseña']

    # Hash de la contraseña
    contraseña_hash = bcrypt.hashpw(contraseña_plana.encode(), bcrypt.gensalt()).decode('utf-8')

    # Insertar academia en Supabase
    try:
        supabase.table("academias").insert({
            "nombre": nombre,
            "email": email,
            "contraseña": contraseña_hash
        }).execute()
        return {"mensaje": "Academia registrada correctamente."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al registrar academia: {str(e)}")

# Endpoint para login de academias desde Supabase
@app.post("/login_academia")
async def login_academia(datos: dict):
    email = datos['email']
    contraseña_plana = datos['contraseña']

    try:
        result = supabase.table("academias").select("*").eq("email", email).execute().data

        if result:
            contraseña_hash = result[0]['contraseña']
            if bcrypt.checkpw(contraseña_plana.encode(), contraseña_hash.encode('utf-8')):
                return {"mensaje": "Inicio de sesión correcto."}
        
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Punto de entrada para Railway (puerto dinámico)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
