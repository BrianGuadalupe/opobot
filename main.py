from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from supabase import create_client
import bcrypt, os, jwt
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

api_key = os.getenv("SAMBANOVA_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "tu_secreto_seguro")  # Asegúrate de tener esto en tu .env

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

def create_token(user_id: str, nombre: str):
    expiration = datetime.utcnow() + timedelta(days=1)
    return jwt.encode(
        {"user_id": user_id, "nombre": nombre, "exp": expiration},
        JWT_SECRET,
        algorithm="HS256"
    )

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

@app.get("/")
def index():
    return FileResponse("frontend/index.html")

@app.post("/pregunta")
async def pregunta(request: Request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="No autorizado")
    
    token = auth_header.split(' ')[1]
    payload = verify_token(token)
    
    datos = await request.json()
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
    contraseña = bcrypt.hashpw(datos['contraseña'].encode(), bcrypt.gensalt()).decode('utf-8')

    # Verificar si el email ya existe
    existing = supabase.table("academias").select("*").eq("email", email).execute().data
    if existing:
        return {"mensaje": "El email ya está registrado."}

    result = supabase.table("academias").insert({
        "nombre": nombre,
        "email": email,
        "contraseña": contraseña
    }).execute()

    if result.data:
        return {"mensaje": "Academia registrada correctamente."}
    return {"mensaje": "Error al registrar la academia."}

@app.post("/login_academia")
async def login_academia(datos: dict):
    email = datos['email']
    contraseña = datos['contraseña']

    result = supabase.table("academias").select("*").eq("email", email).execute().data
    if result and bcrypt.checkpw(contraseña.encode(), result[0]['contraseña'].encode('utf-8')):
        token = create_token(str(result[0]['id']), result[0]['nombre'])
        return {
            "mensaje": "Inicio de sesión correcto.",
            "nombre": result[0]['nombre'],
            "token": token
        }
    return {"mensaje": "Email o contraseña incorrectos."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
