#!/bin/bash
set -e

# Cria um atalho "NutEV" na Area de Trabalho (Desktop) que abre o site local.
# Rode uma vez (duplo-clique). O caminho do projeto fica embutido no atalho.
repo="$(cd "$(dirname "$0")/.." && pwd)"
link="$HOME/Desktop/NutEV.command"

cat > "$link" <<EOF
#!/bin/bash
cd "$repo" || exit 1
exec bash scripts/run_local_unix.sh
EOF
chmod +x "$link"

echo "Atalho criado: $link"
echo "Agora dê duplo-clique em 'NutEV' na sua Area de Trabalho."
