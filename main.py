from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
from supabase import create_client
import bcrypt
import os

load_dotenv()

api_key = os.getenv("SAMBANOVA_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

client = OpenAI(base_url="https://api.sambanova.ai/v1/", api_key=api_key)
supabase = create_client(supabase_url=os.getenv("SUPABASE_URL"), supabase_key=os.getenv("SUPABASE_KEY"))

app = FastAPI()

# Configuración CORS (permite frontend-backend comunicación fácil)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    return FileResponse("frontend/index.html")

@app.post("/pregintar")
async def pregunta(datos: dict):
    pregunta = datos["pregunta"]
    completion = client.chat.completions.create(
        model="Meta-Llama-3.1-405B-Instruct",
        messages=[{"role": "user", "content": pregunta}],
    )
    respuesta = completion.choices[0].message.content
    return {"respuesta": respuesta}

@app.post("/registrar_academia")
async def registrar_academia(datos: dict):
    nombre = datos['nombre']
    email = datos['email']
    contraseña = datos['contraseña'].encode('utf-8')
    contraseña_hash = bcrypt.hashpw(contraseña.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    supabase.table("academias").insert({
        "nombre": nombre,
        "email": email,
        "contraseña": contraseña
    }).execute()

    return {"mensaje": "Academia registrada correctamente"}

@app.post("/login_academia")
async def login_academia(datos: dict):
    email = datos['email']
    contraseña = datos['contraseña']

    result = supabase.table("academias").select("*").eq("email", email).execute()
    academia = result.data

    if academia:
        hash_contraseña = academia[0]['contraseña']
        if bcrypt.checkpw(contraseña.encode('utf-8'), hash.encode()):
            return {"mensaje": "Login exitoso"}
    else:
        return {"mensaje": "Email o contraseña incorrectos"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
