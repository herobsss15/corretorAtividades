from typing import List
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, zipfile, rarfile, json

rarfile.UNRAR_TOOL = r"C:\\Program Files\\WinRAR\\unrar.exe"

from corretor.modelo_ia import gerar_criterios_com_ia, pipeline_gerar_e_avaliar
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
async def avaliar(enunciado: str = Form(...), arquivos: List[UploadFile] = File(...), usar_ia_direta: bool = Form(False)):
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

        with open(arquivo_path, "wb") as f:
            shutil.copyfileobj(arquivo.file, f)

        os.makedirs(aluno_dir, exist_ok=True)

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

    # Gera os critérios para avaliação
    criterios = gerar_criterios_com_ia(enunciado)
    
    # Se usar_ia_direta for True, usa o novo pipeline para cada pasta de aluno
    if usar_ia_direta:
        resultados = {}
        
        for aluno_pasta in os.listdir(UPLOAD_DIR):
            aluno_path = os.path.join(UPLOAD_DIR, aluno_pasta)
            if not os.path.isdir(aluno_path):
                continue
                
            # Concatena todo o código do aluno
            codigo_completo = ""
            for root, _, files in os.walk(aluno_path):
                for file in files:
                    if file.endswith(".cs"):
                        with open(os.path.join(root, file), encoding="utf-8", errors="ignore") as f:
                            codigo_completo += f.read() + "\n\n"
            
            # Usa o pipeline para avaliar
            if codigo_completo:
                try:
                    resultado = pipeline_gerar_e_avaliar(enunciado, codigo_completo)
                    
                    # Processar o resultado da avaliação - corrigir o formato do JSON
                    if isinstance(resultado["avaliacao"], str):
                        # Remover backticks de código e "json" se presentes
                        avaliacao_str = resultado["avaliacao"]
                        avaliacao_str = avaliacao_str.replace("```json", "").replace("```", "").strip()
                        
                        # Tentar converter para JSON
                        try:
                            import json
                            resultado["avaliacao"] = json.loads(avaliacao_str)
                            print(f"Avaliação processada com sucesso para {aluno_pasta}")
                        except json.JSONDecodeError as e:
                            print(f"Erro ao converter JSON para {aluno_pasta}: {str(e)}")
                            print(f"String problemática: {avaliacao_str[:100]}...")
                            resultado["avaliacao_raw"] = avaliacao_str
                            resultado["avaliacao"] = {"erro": "Formato de JSON inválido"}
                    
                    resultados[aluno_pasta] = resultado
                except Exception as e:
                    print(f"Erro ao avaliar {aluno_pasta}: {str(e)}")
                    resultados[aluno_pasta] = {"erro": str(e)}
            else:
                resultados[aluno_pasta] = {"erro": "Nenhum arquivo .cs encontrado"}
                
        return JSONResponse({
            "criterios": criterios,
            "avaliacoes_ia": resultados
        })
    else:
        # Usa o método tradicional de avaliação baseado em palavras-chave
        relatorio = avaliar_entregas(UPLOAD_DIR, criterios)
        return JSONResponse({
            "criterios": criterios,
            "relatorio": relatorio
        })

# Endpoint adicional só para avaliação direta por IA
@app.post("/avaliar-ia")
async def avaliar_ia(enunciado: str = Form(...), codigo: str = Form(...)):
    resultado = pipeline_gerar_e_avaliar(enunciado, codigo)
    return JSONResponse(resultado)
