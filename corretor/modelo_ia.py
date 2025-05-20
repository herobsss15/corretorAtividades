import requests
import os
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# Carrega variáveis do .env
load_dotenv()

# Endpoint e modelo
endpoint = "https://models.github.ai/inference"
model = "deepseek/DeepSeek-V3-0324"  # pode mudar para qualquer outro disponível

# Token GitHub
token = os.getenv("GITHUB_TOKEN")
if not token:
    raise Exception("Variável GITHUB_TOKEN não encontrada no .env")

# Cria cliente da Azure
client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

def gerar_criterios_com_ia(enunciado: str):
    response = client.complete(
        messages=[
            SystemMessage("Você é um corretor de atividades de programação."),
            UserMessage(f"Extraia os critérios de correção do seguinte enunciado:\n\n{enunciado}")
        ],
        temperature=0.7,
        top_p=1.0,
        max_tokens=1000,
        model=model
    )

    return response.choices[0].message.content
