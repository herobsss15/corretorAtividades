from typing import List
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, zipfile, rarfile, json
from datetime import datetime 

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
    """
    Endpoint principal para avaliar entregas de alunos com base em um enunciado.
    
    Args:
        enunciado: Texto descritivo da atividade a ser avaliada
        arquivos: Lista de arquivos ZIP/RAR contendo os códigos dos alunos
        usar_ia_direta: Se True, usa avaliação direta por IA; se False, usa busca por palavras-chave
    """
    # Limpa apenas o diretório de uploads, mantendo o histórico de resultados
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Garantir que o diretório de resultados existe, sem remover seu conteúdo
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

    # *** OTIMIZAÇÃO: GERAR O CHECKLIST APENAS UMA VEZ ***
    # Gera os critérios de avaliação a partir do enunciado uma única vez
    criterios = gerar_criterios_com_ia(enunciado)
    print("Checklist gerado com sucesso!")

    if usar_ia_direta:
        # Método de avaliação direta por IA
        resultados = {}

        # Para cada pasta de aluno
        for aluno_pasta in os.listdir(UPLOAD_DIR):
            aluno_path = os.path.join(UPLOAD_DIR, aluno_pasta)
            if not os.path.isdir(aluno_path):
                continue

            print(f"Avaliando {aluno_pasta}...")
            codigo_completo = ""
            for root, _, files in os.walk(aluno_path):
                for file in files:
                    if file.endswith(".cs"):
                        with open(os.path.join(root, file), encoding="utf-8", errors="ignore") as f:
                            codigo_completo += f.read() + "\n\n"

            if codigo_completo:
                try:
                    # *** OTIMIZAÇÃO: USAR APENAS O MÉTODO DE AVALIAÇÃO ***
                    # Em vez de chamar pipeline_gerar_e_avaliar, chamamos apenas avaliar_codigo_com_criterios
                    # para reutilizar o checklist já gerado
                    from corretor.modelo_ia import avaliar_codigo_com_criterios
                    avaliacao_str = avaliar_codigo_com_criterios(enunciado, criterios, codigo_completo)
                    
                    # Processa o resultado da avaliação
                    avaliacao_json = None
                    try:
                        import json
                        # Primeiro, tentar analisar diretamente
                        avaliacao_json = json.loads(avaliacao_str)
                    except json.JSONDecodeError:
                        # Se falhar, tentar limpar a string
                        try:
                            cleaned_str = avaliacao_str.replace("```json", "").replace("```", "").strip()
                            avaliacao_json = json.loads(cleaned_str)
                        except json.JSONDecodeError as e:
                            avaliacao_json = {
                                "erro": "Falha ao analisar JSON",
                                "mensagem": str(e),
                                "avaliacao_raw": avaliacao_str[:200] + "..." if len(avaliacao_str) > 200 else avaliacao_str
                            }
                    
                    # Agora, montamos o resultado na mesma estrutura que antes
                    resultados[aluno_pasta] = {
                        "checklist": criterios,  # Mesma checklist para todos
                        "avaliacao": avaliacao_json
                    }
                    
                except Exception as e:
                    print(f"Erro ao avaliar {aluno_pasta}: {str(e)}")
                    resultados[aluno_pasta] = {"erro": str(e)}
            else:
                resultados[aluno_pasta] = {"erro": "Nenhum arquivo .cs encontrado"}

        output = {
            "criterios": criterios,
            "avaliacoes_ia": resultados
        }

    else:
        # Método tradicional de avaliação baseado em palavras-chave
        relatorio = avaliar_entregas(UPLOAD_DIR, criterios)
        output = {
            "criterios": criterios,
            "relatorio": relatorio
        }

    # Salvar resultado final com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"resultado_avaliacao_{timestamp}.json"
    output_path = os.path.join(RESULT_DIR, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return JSONResponse(output)

@app.post("/avaliar-ia")
async def avaliar_ia(enunciado: str = Form(...), codigo: str = Form(...)):
    """
    Endpoint para avaliar um único código diretamente.
    Útil para testes e avaliações individuais.
    
    Args:
        enunciado: Texto descritivo da atividade
        codigo: Código-fonte a ser avaliado
    """
    resultado = pipeline_gerar_e_avaliar(enunciado, codigo)
    
    # Salvar também este resultado com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"resultado_ia_direta_{timestamp}.json"
    output_path = os.path.join(RESULT_DIR, output_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    return JSONResponse(resultado)
