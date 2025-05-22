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
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um corretor de programação. Retorne critérios técnicos e objetivos como checklist. "
                    "Cada linha deve começar com '[ ]' seguida por uma frase clara com termos que possam ser detectados no código-fonte. "
                    "Exemplos de aspectos válidos incluem nomes de funções, controle de fluxo, mensagens de saída e lógica condicional. "
                    "Evite frases muito genéricas ou vagas. "
                    "Considere que os nomes das funções podem variar (ex: 'AdicionarCliente' ou 'EntrarNaFila' ao invés de 'Enfileirar')."
                )
            },
            {
                "role": "user",
                "content": f"Avalie este enunciado e extraia os critérios de correção:\n\n{enunciado}",
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
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um avaliador técnico de código em C#. Receberá um enunciado, um checklist técnico e o código-fonte. "
                    "Sua tarefa é verificar, para cada item do checklist, se o código satisfaz aquele critério, mesmo que com nomes ou estruturas diferentes. "
                    "Se a lógica estiver implementada corretamente, considere como 'OK'. Se faltar, marque como 'FALHA'. "
                    "Responda APENAS com um objeto JSON válido, sem formatação markdown, sem explicações adicionais, sem backticks. "
                    "O objeto JSON deve mapear cada critério para seu resultado ('OK' ou 'FALHA')."
                )
            },
            {
                "role": "user",
                "content": f"Enunciado:\n{enunciado}\n\nChecklist:\n{checklist}\n\nCódigo:\n{codigo}",
            }
        ],
        temperature=0.3,
        top_p=1.0,
        max_tokens=1800,
        model=model_name
    )
    return response.choices[0].message.content or ""

# Função pipeline: gera checklist e avalia o código
def pipeline_gerar_e_avaliar(enunciado: str, codigo: str) -> dict:
    checklist = gerar_criterios_com_ia(enunciado)
    avaliacao = avaliar_codigo_com_criterios(enunciado, checklist, codigo)
    return {
        "checklist": checklist,
        "avaliacao": avaliacao
    }
