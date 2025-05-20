from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, zipfile

from corretor.modelo_ia import gerar_criterios_com_ia
from corretor.avaliador import avaliar_entregas

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./uploads"
RESULT_DIR = "./results"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

@app.post("/avaliar")
async def avaliar(enunciado: str = Form(...), arquivos: UploadFile = File(...)):
    # Limpa diretórios antigos
    shutil.rmtree(UPLOAD_DIR)
    shutil.rmtree(RESULT_DIR)
    os.makedirs(UPLOAD_DIR)
    os.makedirs(RESULT_DIR)

    # Salva e extrai entregas
    zip_path = os.path.join(UPLOAD_DIR, str(arquivos.filename))
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(arquivos.file, f)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(UPLOAD_DIR)

    # Gera critérios via IA
    criterios = gerar_criterios_com_ia(enunciado)

    # Avalia todas as entregas extraídas
    relatorio = avaliar_entregas(UPLOAD_DIR, criterios)

    return JSONResponse({"criterios": criterios, "relatorio": relatorio})
