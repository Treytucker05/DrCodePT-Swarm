#!/usr/bin/env bash
set -eo pipefail

# Resolve repo root (parent of this script's directory)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

# Load nvm if available and prefer its Node
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
  . "$NVM_DIR/nvm.sh"
  if command -v nvm >/dev/null 2>&1; then
    nvm use --lts >/dev/null || true
  fi
fi

NODE_PATH=""
if command -v nvm >/dev/null 2>&1; then
  NODE_PATH="$(nvm which --silent || true)"
fi
if [ -z "$NODE_PATH" ] || [ "$NODE_PATH" = "N/A" ]; then
  NODE_PATH="$(command -v node || true)"
fi

if [ -z "$NODE_PATH" ]; then
  echo "node not found in WSL"
  echo "Install Node in WSL (recommended nvm):"
  echo "  sudo apt update && sudo apt install -y curl"
  echo "  curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash"
  echo "  source ~/.bashrc"
  echo "  nvm install --lts"
  exit 127
fi

NODE_BIN="$(dirname "$NODE_PATH")"
CODEX_BIN="$NODE_BIN/codex"

if [ ! -x "$CODEX_BIN" ]; then
  if command -v codex >/dev/null 2>&1; then
    CODEX_BIN="$(command -v codex)"
  else
    echo "codex not found in WSL"
    echo "Install with: npm i -g @openai/codex"
    exit 127
  fi
fi

cd "$REPO_ROOT"
exec "$CODEX_BIN" "$@"
