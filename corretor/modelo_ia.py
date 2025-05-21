import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Token GitHub
token = os.getenv("GITHUB_TOKEN")
if not token:
    raise Exception("Variável GITHUB_TOKEN não encontrada no .env")

# Endpoint e modelo
endpoint = "https://models.github.ai/inference"
model_name = "openai/gpt-4o"

# Cliente OpenAI via GitHub Models
client = OpenAI(
    base_url=endpoint,
    api_key=token,
)

def gerar_criterios_com_ia(enunciado: str):
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "Você é um corretor de programação. Retorne os critérios como checklist simples. "
                    "Cada linha deve iniciar com um verbo no infinitivo e conter no máximo 12 palavras. "
                    "Use o formato '[ ] critério'. Foque em aspectos verificáveis automaticamente como funções, mensagens e lógica de controle de fluxo."
                )
            },
            {
                "role": "user",
                "content": f"Avalie este enunciado e extraia os critérios de correção:\n\n{enunciado}",
            }
        ],
        temperature=0.2,
        top_p=1.0,
        max_tokens=1200,
        model=model_name
    )
    

    return response.choices[0].message.content
