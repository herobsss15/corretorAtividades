import os
import re
import unicodedata

def normalizar_texto(txt):
    txt = txt.lower()
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode('utf-8')
    txt = re.sub(r'[\[\]\*\(\)\.:,\\\"\'""\'\']', '', txt)
    return txt

def extrair_keywords(criterio):
    # Remover o marcador de checklist e limpar o texto
    crit_clean = criterio.replace('[ ]', '').strip()
    crit_clean = normalizar_texto(crit_clean)
    
    # Remover exemplos e textos entre parênteses/aspas
    crit_clean = re.sub(r'"[^"]+"', '', crit_clean)
    crit_clean = re.sub(r'`[^`]+`', '', crit_clean)
    crit_clean = re.sub(r'\(.*?\)', '', crit_clean)
    crit_clean = re.sub(r'exemplo:.*', '', crit_clean)
    crit_clean = re.sub(r'ex:.*', '', crit_clean)
    
    # Lista de palavras a ignorar (stopwords)
    stopwords = {
        'deve', 'como', 'caso', 'exemplo', 'formato', 'programa', 'usuario', 'acao', 'utilizar',
        'uma', 'para', 'que', 'com', 'dos', 'das', 'ou', 'da', 'do', 'em', 'na', 'no', 'aos'
    }
    
    # Extrair palavras significativas (substantivos, verbos)
    palavras = [
        p for p in crit_clean.split()
        if len(p) > 3 and p.isalpha() and p not in stopwords
    ]
    
    # Adicionar algumas palavras-chave comuns de programação se não estiverem presentes
    palavras_prog = {'fila', 'lista', 'array', 'menu', 'cliente', 'adicionar', 'remover', 'exibir'}
    for p in palavras_prog:
        if p in crit_clean and p not in palavras:
            palavras.append(p)
    
    return palavras

def is_criterio_valido(linha):
    return linha.strip().startswith("[ ]") and len(linha.split()) >= 4

def avaliar_entregas(pasta_entregas, criterios_texto):
    resultados = {}

    criterios_linha = [
        c.strip("-• \n")
        for c in criterios_texto.split("\n")
        if is_criterio_valido(c)
    ]

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
            # Um critério é atendido se pelo menos 40% das palavras-chave estão no código
            # e pelo menos uma palavra está presente
            achou = sum(1 for p in palavras if p in texto_codigo) >= max(1, len(palavras) * 0.4)
            resultado_aluno["criterios"][crit] = "OK" if achou else "FALHA"

            if not achou:
                print(f"FALHA em: {crit}")
                print(f"  Palavras-chave: {palavras}")
                nao_encontradas = [p for p in palavras if p not in texto_codigo]
                print(f"  Não encontradas: {nao_encontradas}")

        resultados[aluno_pasta] = resultado_aluno

    return resultados
