from typing import List
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, zipfile, rarfile, json
from datetime import datetime
import time  # Importar o módulo time para gerenciar esperas

rarfile.UNRAR_TOOL = r"C:\\Program Files\\WinRAR\\unrar.exe"

from corretor.modelo_ia import gerar_criterios_com_ia, avaliar_codigo_com_criterios, pipeline_gerar_e_avaliar
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

def get_cached_or_generate_criteria(enunciado):
    """Get criteria from cache or generate new ones"""
    import hashlib
    
    # Create a unique identifier for this prompt
    prompt_hash = hashlib.md5(enunciado.encode()).hexdigest()
    cache_file = os.path.join(RESULT_DIR, f"criteria_cache_{prompt_hash}.txt")
    
    # Check if we have cached criteria
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return f.read()
    
    # Generate new criteria
    criterios = gerar_criterios_com_ia(enunciado)
    
    # Cache the result
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(criterios)
    
    return criterios

def execute_with_rate_limit(func, *args, **kwargs):
    """Execute a function with rate limit handling"""
    import re
    import time
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a rate limit error
            if "RateLimitReached" in error_str:
                wait_time_match = re.search(r'wait (\d+) seconds', error_str)
                if wait_time_match:
                    wait_time = min(int(wait_time_match.group(1)) + 5, 60)
                else:
                    wait_time = 60
                
                print(f"Rate limit reached. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                
                if attempt == max_attempts - 1:
                    raise Exception(f"Failed after {max_attempts} attempts due to rate limits")
            else:
                # For other errors, don't retry
                raise

@app.post("/avaliar")
async def avaliar(enunciado: str = Form(...), 
                  arquivos: List[UploadFile] = File(...), 
                  usar_ia_direta: bool = Form(False)):
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

    # Only generate criteria if needed
    if usar_ia_direta:
        # Generate criteria for AI-direct approach
        criterios = gerar_criterios_com_ia(enunciado)
        print("Checklist gerado com sucesso!")
        
        # Proceed with AI evaluation...
    else:
        # For keyword-based approach, either:
        # 1. Use simpler criteria that don't need AI generation
        criterios = """
        ### Checklist básico
        [ ] Item 1
        [ ] Item 2
        """
        # OR 2. Generate criteria if needed for keyword extraction
        criterios = get_cached_or_generate_criteria(enunciado)
        
        # Proceed with keyword-based evaluation...

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
                tentativas = 0
                max_tentativas = 3
                sucesso = False
                
                while not sucesso and tentativas < max_tentativas:
                    try:
                        avaliacao_str = avaliar_codigo_com_criterios(enunciado, criterios, codigo_completo)
                        try:
                            avaliacao_json = json.loads(avaliacao_str)
                        except json.JSONDecodeError:
                            try:
                                cleaned_str = avaliacao_str.replace("```json", "").replace("```", "").strip()
                                avaliacao_json = json.loads(cleaned_str)
                            except json.JSONDecodeError as e:
                                avaliacao_json = {
                                    "erro": "Falha ao analisar JSON",
                                    "mensagem": str(e),
                                    "avaliacao_raw": avaliacao_str[:200] + "..." if len(avaliacao_str) > 200 else avaliacao_str
                                }
                        resultados[aluno_pasta] = {
                            "checklist": criterios,
                            "avaliacao": avaliacao_json
                        }
                        
                        sucesso = True  # Se chegou aqui, foi bem sucedido
                        
                    except Exception as e:
                        tentativas += 1
                        erro_str = str(e)
                        print(f"Erro ao avaliar {aluno_pasta}: {erro_str}")
                        
                        # Se for um erro de rate limit, esperar o tempo sugerido
                        if "RateLimitReached" in erro_str:
                            # Extrair o tempo de espera da mensagem (em segundos)
                            import re
                            wait_time_match = re.search(r'wait (\d+) seconds', erro_str)
                            if wait_time_match:
                                wait_time = int(wait_time_match.group(1))
                                # Adicionar um pouco de tempo extra para segurança
                                wait_time = min(wait_time + 5, 60)  # Limitar a 60 segundos no máximo
                                print(f"Limite de requisições atingido. Aguardando {wait_time} segundos...")
                                time.sleep(wait_time)
                            else:
                                # Se não conseguir extrair o tempo, esperar 60 segundos
                                print("Limite de requisições atingido. Aguardando 60 segundos...")
                                time.sleep(60)
                        elif tentativas < max_tentativas:
                            # Para outros erros, esperar apenas 5 segundos
                            print(f"Tentando novamente em 5 segundos... (tentativa {tentativas} de {max_tentativas})")
                            time.sleep(5)
                
                # Se não conseguiu avaliar após as tentativas, registrar o erro
                if not sucesso:
                    resultados[aluno_pasta] = {"erro": f"Falha após {max_tentativas} tentativas: {erro_str}"}
            else:
                resultados[aluno_pasta] = {"erro": "Nenhum arquivo .cs encontrado"}

        # Construir o objeto de saída
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
async def avaliar_ia(enunciado: str = Form(...), 
                     codigo: str = Form(...)):
    """
    Endpoint para avaliar um único código diretamente.
    Útil para testes e avaliações individuais.
    
    Args:
        enunciado: Texto descritivo da atividade
        codigo: Código-fonte a ser avaliado
    """
    tentativas = 0
    max_tentativas = 3
    resultado = None
    
    while resultado is None and tentativas < max_tentativas:
        try:
            resultado = pipeline_gerar_e_avaliar(enunciado, codigo)
        except Exception as e:
            tentativas += 1
            erro_str = str(e)
            print(f"Erro ao avaliar código: {erro_str}")
            
            # Se for um erro de rate limit, esperar o tempo sugerido
            if "RateLimitReached" in erro_str:
                import re
                wait_time_match = re.search(r'wait (\d+) seconds', erro_str)
                if wait_time_match:
                    wait_time = int(wait_time_match.group(1))
                    wait_time = min(wait_time + 5, 60)
                    print(f"Limite de requisições atingido. Aguardando {wait_time} segundos...")
                    time.sleep(wait_time)
                else:
                    print("Limite de requisições atingido. Aguardando 60 segundos...")
                    time.sleep(60)
            elif tentativas < max_tentativas:
                print(f"Tentando novamente em 5 segundos... (tentativa {tentativas} de {max_tentativas})")
                time.sleep(5)
    
    # Se todas as tentativas falharem
    if resultado is None:
        resultado = {"erro": f"Falha após {max_tentativas} tentativas: {erro_str}"}
    
    # Salvar também este resultado com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"resultado_ia_direta_{timestamp}.json"
    output_path = os.path.join(RESULT_DIR, output_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    
    return JSONResponse(resultado)
