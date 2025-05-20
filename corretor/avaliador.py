import os
import re
import unicodedata

def normalizar_texto(txt):
    txt = txt.lower()
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode('utf-8')
    txt = re.sub(r'[\[\]\*\(\)\.:,\\\"\'`""'']', '', txt)
    return txt

def extrair_keywords(criterio):
    crit_clean = normalizar_texto(criterio)
    palavras = [p for p in crit_clean.split() if len(p) > 3 and p.isalpha()]
    return palavras

def is_criterio_valido(linha):
    acao = [
        "verificar", "exibir", "remover", "adicionar", "listar", "implementar",
        "usar", "mostrar", "validar", "executar", "criar", "manter", "incluir"
    ]
    linha_n = normalizar_texto(linha)
    return (
        any(verbo in linha_n for verbo in acao)
        and not linha_n.startswith("###")
        and not linha_n.startswith("se ")
        and len(linha.split()) >= 4
    )

def avaliar_entregas(pasta_entregas, criterios_texto):
    resultados = {}

    criterios_linha = [
        c.strip("-• \n")
        for c in criterios_texto.split("\n")
        if is_criterio_valido(c)
    ]
    
    # Log temporário para depuração
    print("Critérios filtrados:")
    for c in criterios_linha:
        print("-", c)
        
    criterios_keywords = {c: extrair_keywords(c) for c in criterios_linha}

    for aluno_pasta in os.listdir(pasta_entregas):
        aluno_path = os.path.join(pasta_entregas, aluno_pasta)
        if not os.path.isdir(aluno_path):
            continue

        resultado_aluno = {"criterios": {}}
        conteudo_total = ""

        for root, _, files in os.walk(aluno_path):
            for file in files:
                if file.endswith(".cs"):
                    with open(os.path.join(root, file), encoding="utf-8", errors="ignore") as f:
                        conteudo_total += f.read().lower() + "\n"

        texto_codigo = normalizar_texto(conteudo_total)

        for crit, palavras in criterios_keywords.items():
            achou = all(p in texto_codigo for p in palavras)
            resultado_aluno["criterios"][crit] = "OK" if achou else "FALHA"

        resultados[aluno_pasta] = resultado_aluno

    return resultados
