#!/usr/bin/env bash
set -euo pipefail
for f in "$HOME/.bash_profile" "$HOME/.zprofile" "$HOME/.zshrc" "$HOME/.bashrc"; do [ -f "$f" ] && source "$f" || true; done
: "${XFYUN_APPID:?Missing XFYUN_APPID}"
: "${XFYUN_API_KEY:?Missing XFYUN_API_KEY}"
: "${XFYUN_API_SECRET:?Missing XFYUN_API_SECRET}"
exec "$@"
