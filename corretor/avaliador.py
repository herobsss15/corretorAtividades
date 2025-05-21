import os
import re
import unicodedata

def normalizar_texto(txt):
    txt = txt.lower()
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode('utf-8')
    txt = re.sub(r'[\[\]\*\(\)\.:,\\\"\'`""\'\']', '', txt)
    return txt

def extrair_keywords(criterio):
    crit_clean = normalizar_texto(criterio)
    crit_clean = re.sub(r'"[^"]+"', '', crit_clean)  # remove aspas e exemplos
    crit_clean = re.sub(r'\`[^\`]+\`', '', crit_clean)  # remove markdown inline code
    crit_clean = re.sub(r'\(.*?\)', '', crit_clean)  # remove parênteses
    palavras = [
        p for p in crit_clean.split()
        if len(p) > 2 and p.isalpha() and p not in {
            'deve', 'como', 'caso', 'exemplo', 'formato', 'mensagem',
            'programa', 'usuario', 'nome', 'acao', 'utilizar', 'cliente', 'fila'
        }
    ]
    return palavras

def is_criterio_valido(linha):
    acao = [
        "verificar", "exibir", "remover", "adicionar", "listar", "implementar",
        "usar", "mostrar", "validar", "executar", "criar", "manter", "incluir"
    ]
    linha_n = normalizar_texto(linha)
    return (
        any(verbo in linha_n for verbo in acao)
        and linha.strip().startswith("[ ]")
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
            achou = sum(1 for p in palavras if p in texto_codigo) >= max(1, len(palavras) * 0.5)
            resultado_aluno["criterios"][crit] = "OK" if achou else "FALHA"

            if not achou:
                print(f"FALHA em: {crit}")
                print(f"  Palavras-chave: {palavras}")
                nao_encontradas = [p for p in palavras if p not in texto_codigo]
                print(f"  Não encontradas: {nao_encontradas}")

        resultados[aluno_pasta] = resultado_aluno

    return resultados
