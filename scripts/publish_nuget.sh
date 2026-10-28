#!/usr/bin/env bash
# Pack + push ISC.Observability to NuGet.org.
#
# Usage:
#   ./scripts/publish_nuget.sh [path-to-env-file]
#
# Reads the API key from a plain file (default: ./env next to this repo's root), WITHOUT
# ever using `source`/`export` on it — this avoids a real bug we hit: a key line whose
# variable-style name contains a hyphen (e.g. "Nuget-api-key=...") is not a valid bash
# identifier, so `source`-ing it makes bash try to RUN it as a command, and bash's
# "command not found" error then echoes the whole line — including the key — to stderr.
# Parsing with grep/cut below never executes file content, so that failure mode is not
# possible here, regardless of what the variable name looks like.
#
# Accepted env-file formats (first match wins):
#   1) A line whose name (before "=") contains "key", any case, hyphens/underscores allowed:
#        Nuget-api-key=xxxxxxxx
#        NUGET_API_KEY=xxxxxxxx
#        api-key=xxxxxxxx
#   2) If no such line exists, the last non-empty line that is NOT itself a "name=value"
#      assignment is treated as the raw key (no variable name at all).
#
# This script never echoes the key. If you need to debug why it's not found, check the
# env file's format yourself — do not add echo/print statements for the resolved value.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CSPROJ="$REPO_DIR/src/ISC.Observability/ISC.Observability.csproj"
ENV_FILE="${1:-$REPO_DIR/env}"
PACK_DIR="$(mktemp -d)"
trap 'rm -rf "$PACK_DIR"' EXIT

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: env file not found at $ENV_FILE" >&2
  exit 1
fi

# --- Resolve the API key, safely (no source/export, no echo of the value) ---------------
API_KEY="$(grep -iE '^[A-Za-z0-9_-]*key[A-Za-z0-9_-]*=' "$ENV_FILE" | head -n1 | cut -d'=' -f2- || true)"
if [ -z "$API_KEY" ]; then
  API_KEY="$(grep -vE '^[A-Za-z0-9_-]+=' "$ENV_FILE" | grep -v '^[[:space:]]*$' | tail -n1 || true)"
fi
# Strip CR (in case the file has Windows line endings) and surrounding whitespace/quotes.
API_KEY="$(printf '%s' "$API_KEY" | tr -d '\r' | sed -e 's/^[[:space:]"'"'"']*//' -e 's/[[:space:]"'"'"']*$//')"

if [ -z "$API_KEY" ]; then
  echo "ERROR: could not find an API key line in $ENV_FILE" >&2
  exit 1
fi
echo "OK: resolved an API key from $ENV_FILE (not printing it)"

# --- Build + pack (Release) --------------------------------------------------------------
echo "Building $CSPROJ (Release)..."
dotnet build "$CSPROJ" -c Release

echo "Packing..."
dotnet pack "$CSPROJ" -c Release --no-build -o "$PACK_DIR"

NUPKG="$(find "$PACK_DIR" -maxdepth 1 -name '*.nupkg' | head -n1)"
if [ -z "$NUPKG" ]; then
  echo "ERROR: pack did not produce a .nupkg file" >&2
  exit 1
fi
echo "Packed: $(basename "$NUPKG")"

# --- Push ---------------------------------------------------------------------------------
echo "Pushing to NuGet.org..."
dotnet nuget push "$NUPKG" \
  --api-key "$API_KEY" \
  --source https://api.nuget.org/v3/index.json \
  --skip-duplicate

echo "Done."
