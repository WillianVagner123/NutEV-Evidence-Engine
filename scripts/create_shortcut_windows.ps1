$ErrorActionPreference = "Stop"

# Cria um atalho "NutEV" na Area de Trabalho apontando para start-nutev.bat.
# Rode uma vez: clique direito neste arquivo > "Executar com PowerShell".
$repo = Split-Path $PSScriptRoot -Parent
$target = Join-Path $repo "start-nutev.bat"
if (-not (Test-Path $target)) { throw "start-nutev.bat nao encontrado em $repo" }

$desktop = [Environment]::GetFolderPath("Desktop")
$linkPath = Join-Path $desktop "NutEV.lnk"

$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($linkPath)
$sc.TargetPath = $target
$sc.WorkingDirectory = $repo
$sc.IconLocation = "shell32.dll,13"
$sc.Description = "Abrir o site NutEV local"
$sc.Save()

Write-Host "Atalho criado: $linkPath"
Read-Host "Pressione Enter para sair"
