# Corretor de Atividades de Programação

Um sistema automatizado para avaliar códigos de alunos iniciantes em programação C#, com suporte a avaliação por IA e análise baseada em palavras-chave.

---

## 🧭 Visão Geral

Este projeto implementa uma **API REST** para correção automática de exercícios de programação.  
O sistema aceita arquivos ZIP/RAR contendo códigos de alunos, extrai e avalia cada submissão com base em critérios técnicos gerados a partir do enunciado do exercício.

---

## 🚀 Recursos Principais

- **Avaliação por IA**: Usa modelos de linguagem avançados para avaliar códigos com base em critérios funcionais  
- **Avaliação por palavras-chave**: Método alternativo que busca termos relevantes no código  
- **Cache de critérios**: Armazena critérios para evitar chamadas repetidas à API  
- **Tratamento de rate limits**: Implementa espera automática quando limites da API são atingidos  
- **Suporte a múltiplos formatos**: Processa arquivos ZIP e RAR contendo projetos C#  

---

## 🛠️ Instalação

### Requisitos
- Python 3.8+
- UnRAR/WinRAR instalado (para extrair arquivos RAR)

### Dependências Python

```bash
pip install fastapi uvicorn python-multipart openai python-dotenv rarfile
````

### Instalação do UnRAR

#### Windows

* Baixe e instale o WinRAR de: [https://www.win-rar.com/](https://www.win-rar.com/)
* Verifique se o caminho do UnRAR está correto no código:

```python
rarfile.UNRAR_TOOL = r"C:\Program Files\WinRAR\unrar.exe"
```

> Ajuste este caminho se sua instalação estiver em local diferente.

#### Linux

```bash
sudo apt-get install unrar
```

#### macOS

```bash
brew install unrar
```

---

## ⚙️ Configuração

1. Clone o repositório
2. Crie um arquivo `.env` na raiz do projeto com seu token do GitHub:

```env
GITHUB_TOKEN=seu_token_github_aqui
```

3. Execute o servidor:

```bash
uvicorn main:app --reload
```

---

## 📚 Guia de Uso

### 🔄 Avaliação em Lote (Múltiplos Alunos)

**Endpoint:** `POST /avaliar`

**Parâmetros:**

* `enunciado`: Texto descritivo do exercício (Form)
* `arquivos`: Arquivos ZIP/RAR com códigos dos alunos (Files)
* `usar_ia_direta`: Boolean para escolher método de avaliação (Form)

**Exemplo com curl:**

```bash
curl -X POST "http://localhost:8000/avaliar" \
-F "enunciado=Crie um programa que solicite o nome do usuário e exiba uma saudação personalizada." \
-F "arquivos=@entregas.zip" \
-F "usar_ia_direta=true"
```

---

### 👤 Avaliação Individual

**Endpoint:** `POST /avaliar-ia`

**Parâmetros:**

* `enunciado`: Texto descritivo do exercício (Form)
* `codigo`: Código-fonte a ser avaliado (Form)

**Exemplo com curl:**

```bash
curl -X POST "http://localhost:8000/avaliar-ia" \
-F "enunciado=Crie um programa que solicite o nome do usuário e exiba uma saudação personalizada." \
-F "codigo=using System; class Program { static void Main() { Console.Write(\"Digite seu nome: \"); var nome = Console.ReadLine(); Console.WriteLine($\"Olá, {nome}!\"); } }"
```

---

## 📁 Estrutura de Arquivos

```
corretorAtividades/
├── corretor/            # Pacote principal de correção
│   ├── __init__.py
│   ├── avaliador.py     # Implementação da avaliação por palavras-chave
│   └── modelo_ia.py     # Integração com a API da OpenAI via GitHub
├── uploads/             # Diretório temporário para arquivos recebidos
├── results/             # Armazena resultados das avaliações
├── .env                 # Variáveis de ambiente (tokens API)
└── main.py              # Aplicação FastAPI principal
```

---

## ⚠️ Limitações Conhecidas

* **Limites de API**: O GitHub impõe limites de 10 chamadas/minuto e 50 chamadas/dia para o modelo GPT-4o
* **Dependência de UnRAR**: Para extrair arquivos RAR, necessita do UnRAR instalado
* **Memória**: Arquivos muito grandes podem causar problemas de memória

---

## 🧯 Troubleshooting

### Erros comuns

* **Rate Limit Exceeded**: Atingiu o limite de requisições à API. O sistema tentará aguardar e repetir a operação.
* **BadZipFile/BadRarFile**: Arquivo corrompido ou formato inválido.
* **RarCannotExec**: UnRAR não está instalado ou não está no caminho correto.

### Solução

Verifique:

* Se o UnRAR está instalado
* Se o caminho está correto em:

```python
rarfile.UNRAR_TOOL = r"caminho/para/seu/unrar"
```

* Se o executável possui permissões de execução

---

## 📈 Melhorias Futuras

* Alternância automática entre modelos diferentes
* Relatório consolidado da turma com estatísticas
* Processamento em lotes para otimizar uso da API
* Interface Web (UI) para facilitar o uso

---

## 🤝 Contribuição

1. Faça um fork do repositório
2. Crie uma branch:

```bash
git checkout -b feature/nova-funcionalidade
```

3. Commit suas mudanças:

```bash
git commit -m 'Adiciona nova funcionalidade'
```

4. Push para o repositório:

```bash
git push origin feature/nova-funcionalidade
```

5. Abra um Pull Request

---

## 🔒 Segurança

> **IMPORTANTE:**
> Não compartilhe seu arquivo `.env` ou token do GitHub.
> Recomendamos criar um token específico para este projeto com permissões limitadas.
