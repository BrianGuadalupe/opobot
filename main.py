from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("SAMBANOVA_API_KEY")
client = OpenAI(base_url="https://api.sambanova.ai/v1/", api_key=api_key)

app = FastAPI()

@app.get("/")
def index():
    return FileResponse("frontend/index.html")

@app.post("/pregunta")
async def pregunta(datos: dict):
    pregunta = datos["pregunta"]
    completion = client.chat.completions.create(
        model="Meta-Llama-3.1-405B-Instruct",
        messages=[{"role": "user", "content": pregunta}],
    )
    respuesta = completion.choices[0].message.content
    return {"respuesta": respuesta}

# IMPORTANTE: Añade estas líneas para Railway
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
