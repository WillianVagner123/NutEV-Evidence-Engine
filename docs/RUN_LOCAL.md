# Rodar o NutEV/NutMEV no PC

Este guia descreve o caminho recomendado para instalar, testar e abrir o sistema localmente.

## 1. Pré-requisitos

Instale no computador:

- Git
- Python 3.12 ou 3.13
- Navegador atualizado

O projeto exige Python `>=3.12,<3.15`.

## 2. Caminho recomendado: instalação automática

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

## 3. Instalação manual

### Baixar o repositório

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

Se o PowerShell bloquear a ativação:

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
python -m pip install -e ".[dashboard,platform]"
```

Esse comando instala:

- `nutev`, a CLI principal;
- dashboard local;
- API local da plataforma.

## 4. Demo local

```bash
nutev demo-data --project-root ./project_output_demo
nutev dashboard --project-root ./project_output_demo --port 8501
```

Depois acesse:

```text
http://127.0.0.1:8501
```

API local:

```bash
nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
```

URLs úteis:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
```

## 5. Verificar instalação

```bash
python scripts/check_local.py
```

No Windows, se estiver usando o ambiente virtual sem ativá-lo:

```powershell
.\.venv\Scripts\python.exe scripts\check_local.py
```

## 6. Rodar o primeiro piloto

Use esta opção quando quiser gerar saída real para trabalho científico:

```bash
nutev --project-root ./project_output_pilot --workstreams busca1 busca2a busca2b a3 --web-enabled
nutev pilot-report --project-root ./project_output_pilot
nutev dashboard --project-root ./project_output_pilot --port 8501
```

Para ambiente instável de rede, rode primeiro em modo controlado:

```powershell
$env:PYTHONPATH="src"
$env:NUTEV_DOWNLOAD_LIMIT="40"
nutev --project-root ./project_output_pilot --workstreams busca1 --web-enabled
```

## 7. Chaves e variáveis locais

Nunca coloque chave de API no GitHub.

### Windows PowerShell

```powershell
$env:OPENAI_API_KEY="sua-chave-aqui"
$env:NCBI_EMAIL="seu-email@exemplo.com"
$env:NCBI_API_KEY="sua-chave-ncbi"
$env:CROSSREF_MAILTO="seu-email@exemplo.com"
$env:OPENALEX_MAILTO="seu-email@exemplo.com"
```

### macOS/Linux

```bash
export OPENAI_API_KEY="sua-chave-aqui"
export NCBI_EMAIL="seu-email@exemplo.com"
export NCBI_API_KEY="sua-chave-ncbi"
export CROSSREF_MAILTO="seu-email@exemplo.com"
export OPENALEX_MAILTO="seu-email@exemplo.com"
```

## 8. Testes essenciais

Caminho padronizado:

```bash
PYTHONPATH=src python -m pytest -q nutev_tests
```

No Windows PowerShell:

```powershell
$env:PYTHONPATH="src"
python -m pytest -q nutev_tests
```

## 9. Artefatos esperados

Em `06_tables`:

- `NUTEV_EVIDENCE_CLAIMS.csv`
- `NUTEV_CLAIM_EVALUATIONS.csv`
- `NUTEV_CONFLICTS.csv`
- `NUTEV_RECOMMENDATION_CANDIDATES.csv`

Em `07_logs`:

- `run_events.jsonl`
- `run_summary.json`
- `run_summary_pretty.txt`
- `search_job_snapshot.json`

Em `10_curated`:

- `curated_metadata.csv`
- `unique_documents.csv`
- `top_operational_documents.xlsx`

## 10. Solução rápida de problemas

### O comando `nutev` não existe

Ative o ambiente virtual e reinstale:

```bash
python -m pip install -e ".[dashboard,platform]"
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

## 11. Observação metodológica

O sistema apoia busca, classificação, auditoria e tradução preliminar de evidências. Ele não substitui revisão humana, avaliação de risco de viés, adjudicação metodológica ou decisão final do protocolo.

`RecommendationCandidate` é recomendação candidata, não recomendação final.
## Robust provider execution

Use `.env.example` as the canonical environment template. `NCBI_EMAIL` is recommended for PubMed, while `NCBI_API_KEY` is optional. If PubMed, Google, SerpAPI, Europe PMC, OpenAlex or Crossref fail, NutEV records the provider event in `07_logs/run_events.jsonl`, `provider_failures.csv` and `provider_performance.csv`, then continues with the remaining providers and official sources.

Resume interrupted searches by re-running the same command; provider checkpoints are stored in `07_logs/checkpoints/` and PubMed continues from the saved `retstart_done` without duplicating collected rows.
