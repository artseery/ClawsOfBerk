#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck disable=SC1091
source "$ROOT/server/pack.env"
RUNTIME="$ROOT/server/runtime"
OLD_ROOT="$HOME/minecraft/atfc/server/runtime"
OLD_UNIT=minecraft-atfc.service
NEW_UNIT=minecraft-clawsofberk.service

fail() { printf 'ClawsOfBerk: %s\n' "$*" >&2; exit 1; }
port_listening() {
  ss -ltnH | awk '{print $4}' | grep -Eq ":$1$"
}
[[ "$ROOT" == "$HOME/minecraft/clawsofberk" ]] || fail "Expected checkout at ~/minecraft/clawsofberk, got $ROOT"
systemctl --user is-active --quiet "$NEW_UNIT" || fail 'Test service is not active; run install.sh first.'
command -v ss >/dev/null 2>&1 || fail 'Install iproute2 (ss is missing) to verify the test listener.'
port_listening "$STAGE_PORT" || fail "Test server is not listening on port $STAGE_PORT yet."

if systemctl --user is-active --quiet "$OLD_UNIT"; then
  systemctl --user stop "$OLD_UNIT"
fi

OLD_SERVER_PROPERTIES="$RUNTIME/server.properties"
ORIGINAL_PROPERTIES=$(mktemp)
cp "$OLD_SERVER_PROPERTIES" "$ORIGINAL_PROPERTIES"
trap 'rm -f "$ORIGINAL_PROPERTIES"' EXIT
sed -i "s/^server-ip=.*/server-ip=/; s/^server-port=.*/server-port=$LIVE_PORT/" "$OLD_SERVER_PROPERTIES"

systemctl --user stop "$NEW_UNIT"
systemctl --user disable "$OLD_UNIT" >/dev/null 2>&1 || true
systemctl --user reset-failed "$NEW_UNIT" >/dev/null 2>&1 || true
if ! systemctl --user start "$NEW_UNIT"; then
  cp "$ORIGINAL_PROPERTIES" "$OLD_SERVER_PROPERTIES"
  systemctl --user enable --now "$OLD_UNIT"
  fail 'New service failed; old ATFC service restarted.'
fi

for _ in $(seq 1 90); do
  if systemctl --user is-active --quiet "$NEW_UNIT" && port_listening "$LIVE_PORT"; then
    systemctl --user enable "$NEW_UNIT" >/dev/null
    printf '%s\n' 'ClawsOfBerk is running on port 25565. The old ATFC runtime and its world remain in place.'
    exit 0
  fi
  if ! systemctl --user is-active --quiet "$NEW_UNIT"; then break; fi
  sleep 2
done

systemctl --user stop "$NEW_UNIT" || true
cp "$ORIGINAL_PROPERTIES" "$OLD_SERVER_PROPERTIES"
systemctl --user enable --now "$OLD_UNIT"
fail 'ClawsOfBerk did not reach Done; old ATFC service restarted.'
