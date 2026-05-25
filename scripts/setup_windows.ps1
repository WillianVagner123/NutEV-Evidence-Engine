<#
.SYNOPSIS
  Instala o NutEV/NutMEV no Windows e prepara uma demo local.

.USAGE
  PowerShell:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\scripts\setup_windows.ps1

Depois rode:
    .\scripts\run_dashboard_windows.ps1
#>

$ErrorActionPreference = "Stop"

function Write-Step($Message) {
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Resolve-Python312 {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        try {
            & py -3.12 --version | Out-Null
            return @("py", "-3.12")
        } catch {
            Write-Host "Python 3.12 nao encontrado pelo launcher py." -ForegroundColor Yellow
        }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $versionText = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        $parts = $versionText.Split('.')
        $major = [int]$parts[0]
        $minor = [int]$parts[1]
        if ($major -eq 3 -and $minor -ge 12 -and $minor -lt 15) {
            return @("python")
        }
    }

    throw "Instale Python 3.12 ou 3.13 e tente novamente: https://www.python.org/downloads/"
}

if (-not (Test-Path "pyproject.toml")) {
    throw "Execute este script dentro da pasta raiz do repositorio NUT-MEV_NEW."
}

Write-Step "Validando Python"
$pythonBase = Resolve-Python312
Write-Host "Python selecionado: $($pythonBase -join ' ')"

Write-Step "Criando ambiente virtual .venv"
if (-not (Test-Path ".venv")) {
    & $pythonBase[0] @($pythonBase[1..($pythonBase.Length - 1)]) -m venv .venv
}

$VenvPython = Join-Path ".venv" "Scripts\python.exe"
$VenvNutev = Join-Path ".venv" "Scripts\nutev.exe"

Write-Step "Atualizando pip"
& $VenvPython -m pip install --upgrade pip

Write-Step "Instalando NutEV/NutMEV com dashboard e API"
& $VenvPython -m pip install -e ".[dashboard,platform]"

Write-Step "Instalando navegador Chromium do Playwright quando disponivel"
try {
    & $VenvPython -m playwright install chromium
} catch {
    Write-Host "Aviso: Playwright Chromium nao foi instalado automaticamente. O dashboard e a demo ainda podem funcionar; para captura web, rode depois: .\.venv\Scripts\python.exe -m playwright install chromium" -ForegroundColor Yellow
}

Write-Step "Gerando dados demo"
& $VenvNutev demo-data --project-root ./project_output_demo

Write-Step "Checando instalacao"
& $VenvPython scripts/check_local.py

Write-Host "`nPronto. Para abrir o dashboard:" -ForegroundColor Green
Write-Host "  .\scripts\run_dashboard_windows.ps1"
Write-Host "`nPara abrir a API local:" -ForegroundColor Green
Write-Host "  .\scripts\run_api_windows.ps1"
