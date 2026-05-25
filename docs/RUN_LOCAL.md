# Rodar o NutEV/NutMEV no PC

Este guia é o caminho recomendado para instalar, testar e abrir o sistema localmente.

## 1. Pré-requisitos

Instale no computador:

- Git
- Python 3.12 ou 3.13
- Navegador atualizado

O projeto exige Python `>=3.12,<3.15`.

## 2. Baixar o repositório

```bash
git clone https://github.com/WillianVagner123/NUT-MEV_NEW.git
cd NUT-MEV_NEW
```

## 3. Criar ambiente virtual

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Se o PowerShell bloquear a ativação:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### macOS/Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 4. Instalar o sistema

```bash
pip install -e ".[dashboard,platform]"
```

Esse comando instala o pacote em modo editável e habilita:

- `nutev`, a CLI principal;
- dashboard local;
- API local da plataforma.

## 5. Gerar dados demo

```bash
nutev demo-data --project-root ./project_output_demo
```

## 6. Abrir o dashboard

```bash
nutev dashboard --project-root ./project_output_demo --port 8501
```

Depois acesse:

```text
http://127.0.0.1:8501
```

## 7. Abrir a API local

Em outro terminal, com o ambiente virtual ativado:

```bash
nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
```

URLs úteis:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

## 8. Rodar o primeiro piloto

Use esta opção quando quiser gerar saída real para trabalho científico:

```bash
nutev --project-root ./project_output_pilot --workstreams busca1 busca2a busca2b a3 --web-enabled
nutev pilot-report --project-root ./project_output_pilot
nutev dashboard --project-root ./project_output_pilot --port 8501
```

## 9. Chaves e variáveis locais

Nunca coloque chave de API no GitHub.

### Windows PowerShell

```powershell
$env:OPENAI_API_KEY="sua-chave-aqui"
```

### macOS/Linux

```bash
export OPENAI_API_KEY="sua-chave-aqui"
```

Variáveis úteis para integrações bibliográficas:

```bash
export NCBI_EMAIL="seu-email@exemplo.com"
export NCBI_API_KEY="sua-chave-ncbi"
export CROSSREF_MAILTO="seu-email@exemplo.com"
export OPENALEX_MAILTO="seu-email@exemplo.com"
```

## 10. Testes essenciais

```bash
PYTHONPATH=src python -m pytest -q tests/nutev
```

No Windows PowerShell:

```powershell
$env:PYTHONPATH="src"
python -m pytest -q tests/nutev
```

## 11. Solução rápida de problemas

### O comando `nutev` não existe

Ative o ambiente virtual e reinstale:

```bash
pip install -e ".[dashboard,platform]"
```

### Erro de versão do Python

Confirme:

```bash
python --version
```

Use Python 3.12 ou 3.13.

### Dashboard não abre

Confirme se a porta está correta:

```bash
nutev dashboard --project-root ./project_output_demo --port 8501
```

Depois acesse `http://127.0.0.1:8501`.

### API não abre

Rode:

```bash
nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
```

Depois acesse `http://127.0.0.1:8000/docs`.

## 12. Regra metodológica

O sistema gera evidências candidatas, matrizes, logs e relatórios de apoio. Ele não substitui revisão humana, adjudicação metodológica ou decisão final do protocolo NutEV/NutMEV.
