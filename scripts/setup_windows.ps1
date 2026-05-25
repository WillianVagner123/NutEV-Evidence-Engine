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

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Comando falhou com codigo ${LASTEXITCODE}: $Command $($Arguments -join ' ')"
    }
}

function Invoke-PythonBase {
    param(
        [Parameter(Mandatory = $true)][string[]]$PythonBase,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    $cmd = $PythonBase[0]
    $prefixArgs = @()
    if ($PythonBase.Length -gt 1) {
        $prefixArgs = $PythonBase[1..($PythonBase.Length - 1)]
    }
    Invoke-Checked $cmd @($prefixArgs + $Arguments)
}

function Resolve-Python312 {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        try {
            & py -3.12 --version | Out-Null
            if ($LASTEXITCODE -eq 0) {
                return @("py", "-3.12")
            }
        } catch {
            Write-Host "Python 3.12 nao encontrado pelo launcher py." -ForegroundColor Yellow
        }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $versionText = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        if ($LASTEXITCODE -eq 0) {
            $parts = $versionText.Split('.')
            $major = [int]$parts[0]
            $minor = [int]$parts[1]
            if ($major -eq 3 -and $minor -ge 12 -and $minor -lt 15) {
                return @("python")
            }
        }
    }

    throw "Instale Python 3.12 ou 3.13 e tente novamente: https://www.python.org/downloads/"
}

function Test-ProjectPathLength {
    $rootPath = (Resolve-Path ".").Path
    Write-Host "Pasta atual: $rootPath"

    if ($rootPath.Length -gt 80) {
        Write-Host "" -ForegroundColor Yellow
        Write-Host "ATENCAO: o caminho desta pasta esta longo demais para algumas dependencias no Windows." -ForegroundColor Yellow
        Write-Host "Comprimento atual: $($rootPath.Length) caracteres." -ForegroundColor Yellow
        Write-Host "Caminho recomendado: C:\NutMEV\NUT-MEV_NEW" -ForegroundColor Yellow
        Write-Host "" -ForegroundColor Yellow
        Write-Host "Correcao rapida:" -ForegroundColor Yellow
        Write-Host "  cd C:\" -ForegroundColor Yellow
        Write-Host "  mkdir NutMEV" -ForegroundColor Yellow
        Write-Host "  cd C:\NutMEV" -ForegroundColor Yellow
        Write-Host "  git clone https://github.com/WillianVagner123/NUT-MEV_NEW.git" -ForegroundColor Yellow
        Write-Host "  cd NUT-MEV_NEW" -ForegroundColor Yellow
        Write-Host "  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass" -ForegroundColor Yellow
        Write-Host "  .\scripts\setup_windows.ps1" -ForegroundColor Yellow
        throw "Caminho longo detectado. Mova ou clone o projeto para C:\NutMEV\NUT-MEV_NEW e rode novamente."
    }
}

if (-not (Test-Path "pyproject.toml")) {
    throw "Execute este script dentro da pasta raiz do repositorio NUT-MEV_NEW."
}

Write-Step "Validando caminho do projeto"
Test-ProjectPathLength

Write-Step "Configurando Git para aceitar caminhos longos neste usuario"
try {
    git config --global core.longpaths true
} catch {
    Write-Host "Aviso: nao consegui configurar git core.longpaths. Continue se o projeto estiver em C:\NutMEV\NUT-MEV_NEW." -ForegroundColor Yellow
}

Write-Step "Validando Python"
$pythonBase = Resolve-Python312
Write-Host "Python selecionado: $($pythonBase -join ' ')"

Write-Step "Criando ambiente virtual .venv"
if (-not (Test-Path ".venv")) {
    Invoke-PythonBase -PythonBase $pythonBase -Arguments @("-m", "venv", ".venv")
}

$VenvPython = Join-Path ".venv" "Scripts\python.exe"
$VenvNutev = Join-Path ".venv" "Scripts\nutev.exe"

Write-Step "Atualizando pip"
Invoke-Checked $VenvPython -m pip install --upgrade pip

Write-Step "Instalando NutEV/NutMEV com dashboard e API"
Invoke-Checked $VenvPython -m pip install --no-cache-dir -e ".[dashboard,platform]"

Write-Step "Instalando navegador Chromium do Playwright quando disponivel"
try {
    Invoke-Checked $VenvPython -m playwright install chromium
} catch {
    Write-Host "Aviso: Playwright Chromium nao foi instalado automaticamente. O dashboard e a demo ainda podem funcionar; para captura web, rode depois: .\.venv\Scripts\python.exe -m playwright install chromium" -ForegroundColor Yellow
}

Write-Step "Gerando dados demo"
Invoke-Checked $VenvNutev demo-data --project-root ./project_output_demo

Write-Step "Checando instalacao"
Invoke-Checked $VenvPython scripts/check_local.py

Write-Host "`nPronto. Para abrir o dashboard:" -ForegroundColor Green
Write-Host "  .\scripts\run_dashboard_windows.ps1"
Write-Host "`nPara abrir a API local:" -ForegroundColor Green
Write-Host "  .\scripts\run_api_windows.ps1"
