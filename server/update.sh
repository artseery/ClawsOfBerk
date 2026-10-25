#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck disable=SC1091
source "$ROOT/server/pack.env"
RUNTIME="$ROOT/server/runtime"
UNIT=minecraft-clawsofberk.service
fail() { printf 'ClawsOfBerk: %s\n' "$*" >&2; exit 1; }

[[ "$ROOT" == "$HOME/minecraft/clawsofberk" ]] || fail "Expected checkout at ~/minecraft/clawsofberk, got $ROOT"
if [[ -r "$RUNTIME/java.env" ]]; then
  # shellcheck disable=SC1090
  source "$RUNTIME/java.env"
fi
[[ -f "$RUNTIME/packwiz-installer-bootstrap.jar" ]] || fail 'Run server/install.sh first.'
[[ -f "$RUNTIME/run.sh" ]] || fail 'Forge runtime is missing.'
JAVA_BIN=${JAVA_BIN:-/usr/lib/jvm/java-17-openjdk-amd64/bin/java}
[[ -x "$JAVA_BIN" ]] || JAVA_BIN=$(command -v java || true)
[[ -n "$JAVA_BIN" && -x "$JAVA_BIN" ]] || fail 'Java 17 is not available.'
java_version=$("$JAVA_BIN" -version 2>&1 | awk -F '"' '/version/ {print $2; exit}')
[[ "$java_version" == "$JAVA_MAJOR".* ]] || fail "Java $JAVA_MAJOR is required; found ${java_version:-unknown}"

WAS_ACTIVE=false
if systemctl --user is-active --quiet "$UNIT"; then
  WAS_ACTIVE=true
  systemctl --user stop "$UNIT"
fi

if ! (cd "$RUNTIME" && "$JAVA_BIN" -jar packwiz-installer-bootstrap.jar -g -s server "$PACK_URL"); then
  printf '%s\n' 'Pack sync failed; service remains stopped so the partial update is not launched.' >&2
  exit 1
fi

if [[ "$WAS_ACTIVE" == true ]]; then
  systemctl --user reset-failed "$UNIT"
  systemctl --user start "$UNIT"
fi
