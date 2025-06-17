import os
from dotenv import load_dotenv
from openai import OpenAI

# Carregar variáveis de ambiente
load_dotenv()

# Token GitHub
token = os.getenv("GITHUB_TOKEN")
if not token:
    raise Exception("Variável GITHUB_TOKEN não encontrada no .env")

# Configuração do modelo e cliente
endpoint = "https://models.github.ai/inference"
model_name = "openai/gpt-4o"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)

# Função para gerar os critérios de avaliação (checklist)
def gerar_criterios_com_ia(enunciado: str) -> str:
    """
    Gera critérios de avaliação (checklist) a partir do enunciado usando IA.
    
    Args:
        enunciado: Texto do enunciado da atividade
    
    Returns:
        String contendo os critérios de avaliação em formato de checklist
    """
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um professor de programação para iniciantes elaborando critérios de avaliação. "
                    "Crie um checklist de critérios técnicos claros e objetivos para avaliar códigos de estudantes que estão começando a programar. "
                    
                    "Regras para criar os critérios:\n"
                    "1. Organize os critérios em categorias (Ex: 'Entrada de dados', 'Processamento', 'Saída').\n"
                    "2. Cada linha deve começar com '[ ]' seguida por uma frase clara e específica.\n"
                    "3. Foque em comportamentos essenciais que podem ser verificados no código.\n"
                    "4. Inclua exemplos alternativos em parênteses (Ex: 'usar uma estrutura de repetição (ex: `for`, `while` ou `do-while`)').\n"
                    "5. Considere que alunos iniciantes usarão nomes de variáveis e funções diversos.\n"
                    "6. Evite critérios excessivamente rígidos em relação à formatação de saída ou estilo.\n"
                    "7. Priorize a funcionalidade básica sobre otimização ou boas práticas avançadas.\n"
                    "8. Limite-se a no máximo 10 critérios essenciais para não sobrecarregar a avaliação.\n"
                    
                    "Sua checklist deve ajudar a avaliar se o aluno entendeu e implementou os conceitos básicos necessários, "
                    "sem esperar código perfeito ou otimizado."
                )
            },
            {
                "role": "user",
                "content": f"Crie critérios de avaliação para este enunciado de exercício para alunos iniciantes:\n\n{enunciado}",
            }
        ],
        temperature=0.5,
        top_p=1.0,
        max_tokens=1500,
        model=model_name
    )
    return response.choices[0].message.content or ""

# Função para avaliar o código com base no checklist gerado
def avaliar_codigo_com_criterios(enunciado: str, checklist: str, codigo: str) -> str:
    """
    Avalia um código-fonte com base em um checklist de critérios.
    
    Args:
        enunciado: Texto do enunciado da atividade
        checklist: Lista de critérios para avaliar o código
        codigo: Código-fonte a ser avaliado
    
    Returns:
        String em formato JSON com os resultados da avaliação
    """
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um avaliador técnico de código em C# para estudantes iniciantes em programação. "
                    "Receberá um enunciado, um checklist técnico e o código-fonte submetido por um aluno que está começando. "
                    "Seu objetivo é avaliar se o código atende aos requisitos básicos, sem esperar soluções avançadas ou otimizadas. "
                    "Lembre-se que são códigos de pessoas iniciando na área de programação, então:\n\n"
                    
                    "1. Seja generoso em sua avaliação, focando na funcionalidade básica:\n"
                    "   - Se o código implementa a lógica necessária e funciona, mesmo que não seja a implementação ideal, considere 'OK'\n"
                    "   - Nomes de variáveis, funções e estruturas podem ser simples ou mesmo não seguir convenções\n"
                    "   - A presença de código extra ou passos desnecessários é aceitável, desde que não prejudique a funcionalidade\n\n"
                    
                    "2. Seja muito flexível com detalhes de formato e estilo:\n"
                    "   - Pequenas variações em mensagens de saída são aceitáveis (ex: 'Olá João' vs 'Olá, João!')\n"
                    "   - É normal ter espaços extras, capitalização diferente ou pontuação variada\n"
                    "   - Mensagens de orientação ao usuário extras são permitidas (ex: 'Digite seu nome:')\n\n"
                    
                    "3. Concentre-se no essencial para iniciantes:\n"
                    "   - Para entrada de dados: verifica se o código captura as informações necessárias\n"
                    "   - Para processamento: verifica se a lógica básica está presente e produz resultados corretos\n"
                    "   - Para saída: verifica se as informações essenciais são apresentadas, mesmo com formatação diferente\n\n"
                    
                    "Responda APENAS com um objeto JSON válido sem formatação markdown, explicações adicionais ou backticks. "
                    "O objeto JSON deve mapear cada critério para seu resultado ('OK' ou 'FALHA')."
                )
            },
            {
                "role": "user",
                "content": f"Enunciado:\n{enunciado}\n\nChecklist:\n{checklist}\n\nCódigo:\n{codigo}",
            }
        ],
        temperature=0.25,
        top_p=1.0,
        max_tokens=1800,
        model=model_name
    )
    return response.choices[0].message.content or ""

# Função pipeline: gera checklist e avalia o código
def pipeline_gerar_e_avaliar(enunciado: str, codigo: str) -> dict:
    """
    Pipeline completo: gera critérios de avaliação e avalia o código.
    
    Args:
        enunciado: Texto do enunciado da atividade
        codigo: Código-fonte a ser avaliado
    
    Returns:
        Dicionário contendo o checklist e a avaliação
    """
    import json
    
    # Gera os critérios de avaliação
    checklist = gerar_criterios_com_ia(enunciado)
    
    # Avalia o código com base nos critérios
    avaliacao_str = avaliar_codigo_com_criterios(enunciado, checklist, codigo)
    
    # Processa o resultado da avaliação
    avaliacao_json = None
    try:
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
    
    # Constrói o resultado base
    resultado = {
        "checklist": checklist,
        "avaliacao": avaliacao_json
    }
    
    return resultado
