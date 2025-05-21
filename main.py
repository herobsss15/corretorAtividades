from typing import List
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, zipfile, rarfile

rarfile.UNRAR_TOOL = r"C:\Program Files\WinRAR\unrar.exe"

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
async def avaliar(enunciado: str = Form(...), arquivos: List[UploadFile] = File(...)):
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    shutil.rmtree(RESULT_DIR, ignore_errors=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)

    for arquivo in arquivos:
        if not arquivo.filename:
            continue            
        
        nome_arquivo = str(arquivo.filename)
        arquivo_path = os.path.join(UPLOAD_DIR, nome_arquivo)
        extensao = os.path.splitext(nome_arquivo)[1].lower()
        aluno_dir = os.path.join(UPLOAD_DIR, os.path.splitext(nome_arquivo)[0])
        
        # Salva o arquivo
        with open(arquivo_path, "wb") as f:
            shutil.copyfileobj(arquivo.file, f)
        
        # Cria o diretório para extrair os arquivos
        os.makedirs(aluno_dir, exist_ok=True)
        
        # Extrai o conteúdo baseado na extensão
        if extensao == '.zip':
            try:
                with zipfile.ZipFile(arquivo_path, 'r') as zip_ref:
                    zip_ref.extractall(aluno_dir)
            except zipfile.BadZipFile:
                print(f"Erro ao extrair {nome_arquivo}: arquivo ZIP inválido")
        elif extensao == '.rar':
            try:
                with rarfile.RarFile(arquivo_path, 'r') as rar_ref:
                    rar_ref.extractall(aluno_dir)
            except rarfile.BadRarFile:
                print(f"Erro ao extrair {nome_arquivo}: arquivo RAR inválido")
            except rarfile.RarCannotExec:
                print(f"Erro ao extrair {nome_arquivo}: necessário instalar UnRAR")
        else:
            print(f"Formato não suportado: {extensao}")

    criterios = gerar_criterios_com_ia(enunciado)
    relatorio = avaliar_entregas(UPLOAD_DIR, criterios)

    return JSONResponse({"criterios": criterios, "relatorio": relatorio})
