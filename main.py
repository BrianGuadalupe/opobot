from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from supabase import create_client
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("SAMBANOVA_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(base_url="https://api.sambanova.ai/v1/", api_key=api_key)

app = FastAPI()

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

@app.post("/pregunta")
async def pregunta(datos: dict):
    pregunta_usuario = datos["pregunta"]

    system_prompt = (
        "Eres Opobot, un asistente virtual especializado en ayudar a estudiantes a prepararse para oposiciones en España. "
        "Debes responder de manera clara, estructurada, y fundamentada en legislación vigente española, normativas oficiales y contenidos académicos. "
        "Si desconoces la respuesta exacta, indica claramente que no dispones de esa información. "
        "Usa un tono formal pero accesible, organizado en puntos o párrafos breves para una mejor comprensión."
    )

    completion = client.chat.completions.create(
        model="Meta-Llama-3.1-405B-Instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": pregunta_usuario}
        ],
    )
    respuesta = completion.choices[0].message.content
    return {"respuesta": respuesta}

@app.post("/registrar_academia")
async def registrar_academia(datos: dict):
    nombre = datos['nombre']
    email = datos['email']
    contraseña = bcrypt.hashpw(datos['contraseña'].encode(), bcrypt.gensalt()).decode('utf-8')

    supabase.table("academias").insert({
        "nombre": nombre,
        "email": email,
        "contraseña": contraseña
    }).execute()

    return {"mensaje": "Academia registrada correctamente."}

@app.post("/login_academia")
async def login_academia(datos: dict):
    email = datos['email']
    contraseña = datos['contraseña']

    result = supabase.table("academias").select("*").eq("email", email).execute().data
    if result and bcrypt.checkpw(contraseña.encode(), result[0]['contraseña'].encode('utf-8')):
        return {"mensaje": "Inicio de sesión correcto."}
    return {"mensaje": "Email o contraseña incorrectos."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

