import requests
import os

GITHUB_MODEL_API_URL = "https://api.githubcopilot.com/chat/completions"
GITHUB_PAT = os.getenv("GITHUB_PAT")
def gerar_criterios_com_ia(enunciado: str):
    if not GITHUB_PAT:
        raise Exception("Variável de ambiente GITHUB_PAT não definida")

    payload = {
        "model": "gpt-4",  # ou "gpt-4-1106-preview" se preferir especificar
        "messages": [
            {
                "role": "system",
                "content": "Você é um avaliador de atividades de programação. Converta o enunciado em critérios de avaliação claros e objetivos, como: estrutura de classes, métodos obrigatórios, regras de negócio, etc."
            },
            {
                "role": "user",
                "content": f"Enunciado da atividade:\n\n{enunciado}"
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {GITHUB_PAT}",
        "Content-Type": "application/json"
    }

    response = requests.post(GITHUB_MODEL_API_URL, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception(f"Erro na API GitHub Model: {response.status_code} - {response.text}")
