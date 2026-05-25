# Rodar o NutEV/NutMEV no PC

Este guia e o caminho recomendado para instalar, testar e abrir o sistema localmente.

## 1. Pre-requisitos

Instale no computador:

- Git
- Python 3.12 ou 3.13
- Navegador atualizado

O projeto exige Python `>=3.12,<3.15`.

## 2. Caminho recomendado: instalacao automatica

### Windows PowerShell

```powershell
git clone https://github.com/WillianVagner123/NUT-MEV_NEW.git
cd NUT-MEV_NEW
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup_windows.ps1
```

Depois abra o dashboard:

```powershell
.\scripts\run_dashboard_windows.ps1
```

Acesse:

```text
http://127.0.0.1:8501
```

Para abrir a API local em outro terminal:

```powershell
.\scripts\run_api_windows.ps1
```

Acesse:

```text
http://127.0.0.1:8000/docs
```

### macOS/Linux

```bash
git clone https://github.com/WillianVagner123/NUT-MEV_NEW.git
cd NUT-MEV_NEW
chmod +x scripts/setup_unix.sh scripts/run_dashboard_unix.sh
./scripts/setup_unix.sh
```

Depois abra o dashboard:

```bash
./scripts/run_dashboard_unix.sh
```

Acesse:

```text
http://127.0.0.1:8501
```

Para abrir a API local em outro terminal:

```bash
.venv/bin/nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
```

Acesse:

```text
http://127.0.0.1:8000/docs
```

## 3. Instalacao manual

Use esta secao se preferir controlar cada etapa.

### Baixar o repositorio

```bash
git clone https://github.com/WillianVagner123/NUT-MEV_NEW.git
cd NUT-MEV_NEW
```

### Criar ambiente virtual

#### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Se o PowerShell bloquear a ativacao:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

#### macOS/Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

### Instalar o sistema

```bash
pip install -e ".[dashboard,platform]"
```

Esse comando instala o pacote em modo editavel e habilita:

- `nutev`, a CLI principal;
- dashboard local;
- API local da plataforma.

### Gerar dados demo

```bash
nutev demo-data --project-root ./project_output_demo
```

### Abrir o dashboard

```bash
nutev dashboard --project-root ./project_output_demo --port 8501
```

Depois acesse:

```text
http://127.0.0.1:8501
```

### Abrir a API local

Em outro terminal, com o ambiente virtual ativado:

```bash
nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
```

URLs uteis:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

## 4. Verificar instalacao

```bash
python scripts/check_local.py
```

No Windows, se estiver usando o ambiente virtual sem ativa-lo:

```powershell
.\.venv\Scripts\python.exe scripts\check_local.py
```

## 5. Rodar o primeiro piloto

Use esta opcao quando quiser gerar saida real para trabalho cientifico:

```bash
nutev --project-root ./project_output_pilot --workstreams busca1 busca2a busca2b a3 --web-enabled
nutev pilot-report --project-root ./project_output_pilot
nutev dashboard --project-root ./project_output_pilot --port 8501
```

## 6. Chaves e variaveis locais

Nunca coloque chave de API no GitHub.

### Windows PowerShell

```powershell
$env:OPENAI_API_KEY="sua-chave-aqui"
```

### macOS/Linux

```bash
export OPENAI_API_KEY="sua-chave-aqui"
```

Variaveis uteis para integracoes bibliograficas:

```bash
export NCBI_EMAIL="seu-email@exemplo.com"
export NCBI_API_KEY="sua-chave-ncbi"
export CROSSREF_MAILTO="seu-email@exemplo.com"
export OPENALEX_MAILTO="seu-email@exemplo.com"
```

## 7. Testes essenciais

```bash
PYTHONPATH=src python -m pytest -q tests/nutev
```

No Windows PowerShell:

```powershell
$env:PYTHONPATH="src"
python -m pytest -q tests/nutev
```

## 8. Solucao rapida de problemas

### O comando `nutev` nao existe

Ative o ambiente virtual e reinstale:

```bash
pip install -e ".[dashboard,platform]"
```

Ou rode o verificador:

```bash
python scripts/check_local.py
```

### Erro de versao do Python

Confirme:

```bash
python --version
```

Use Python 3.12 ou 3.13.

### Dashboard nao abre

Confirme se a porta esta correta:

```bash
nutev dashboard --project-root ./project_output_demo --port 8501
```

Depois acesse `http://127.0.0.1:8501`.

### API nao abre

Rode:

```bash
nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
```

Depois acesse `http://127.0.0.1:8000/docs`.

## 9. Regra metodologica

O sistema gera evidencias candidatas, matrizes, logs e relatorios de apoio. Ele nao substitui revisao humana, adjudicacao metodologica ou decisao final do protocolo NutEV/NutMEV.
