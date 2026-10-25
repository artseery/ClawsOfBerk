#!/usr/bin/env bash
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck disable=SC1091
source "$ROOT/server/pack.env"

fail() { printf 'ClawsOfBerk: %s\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"; }
verify_sha256() {
  local actual
  actual=$(sha256sum "$2" | awk '{print $1}')
  [[ "$actual" == "$1" ]] || fail "SHA-256 mismatch: $2"
}
verify_sha1() {
  local actual
  actual=$(sha1sum "$2" | awk '{print $1}')
  [[ "$actual" == "$1" ]] || fail "SHA-1 mismatch: $2"
}

[[ "$ROOT" == "$HOME/minecraft/clawsofberk" ]] || fail "Expected checkout at ~/minecraft/clawsofberk, got $ROOT"
[[ "$PACK_URL" == https://* ]] || fail 'PACK_URL must use HTTPS'
for tool in curl sha256sum sha1sum awk systemctl grep readlink; do need "$tool"; done

JAVA_BIN=${JAVA_BIN:-/usr/lib/jvm/java-17-openjdk-amd64/bin/java}
[[ -x "$JAVA_BIN" ]] || JAVA_BIN=$(command -v java || true)
[[ -n "$JAVA_BIN" && -x "$JAVA_BIN" ]] || fail 'Install Java 17 or set JAVA_BIN to its java executable.'
java_version=$("$JAVA_BIN" -version 2>&1 | awk -F '"' '/version/ {print $2; exit}')
[[ "$java_version" == "$JAVA_MAJOR".* ]] || fail "Java $JAVA_MAJOR is required; found ${java_version:-unknown} at $JAVA_BIN"

RUNTIME="$ROOT/server/runtime"
mkdir -p "$RUNTIME"
JAVA_HOME=$(dirname "$(dirname "$(readlink -f "$JAVA_BIN")")")
JAVA_DIR=$(dirname "$(readlink -f "$JAVA_BIN")")
cat > "$RUNTIME/java.env" <<EOF
JAVA_HOME=$JAVA_HOME
PATH=$JAVA_DIR:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
EOF

BOOTSTRAP="$RUNTIME/packwiz-installer-bootstrap.jar"
if [[ ! -f "$BOOTSTRAP" ]]; then
  curl --fail --location --retry 3 --retry-all-errors --output "$BOOTSTRAP.part" "$PACKWIZ_BOOTSTRAP_URL"
  verify_sha256 "$PACKWIZ_BOOTSTRAP_SHA256" "$BOOTSTRAP.part"
  mv "$BOOTSTRAP.part" "$BOOTSTRAP"
else
  verify_sha256 "$PACKWIZ_BOOTSTRAP_SHA256" "$BOOTSTRAP"
fi

printf '%s\n' 'Syncing server files from the GitHub Pages Packwiz manifest...'
(cd "$RUNTIME" && "$JAVA_BIN" -jar "$BOOTSTRAP" -g -s server "$PACK_URL")

FORGE_INSTALLER="$RUNTIME/.forge-$FORGE_VERSION-installer.jar"
if [[ ! -f "$RUNTIME/run.sh" ]]; then
  curl --fail --location --retry 3 --retry-all-errors --output "$FORGE_INSTALLER.part" "$FORGE_INSTALLER_URL"
  verify_sha1 "$FORGE_INSTALLER_SHA1" "$FORGE_INSTALLER.part"
  mv "$FORGE_INSTALLER.part" "$FORGE_INSTALLER"
  (cd "$RUNTIME" && "$JAVA_BIN" -jar "$FORGE_INSTALLER" --installServer)
fi
[[ -x "$RUNTIME/run.sh" || -f "$RUNTIME/run.sh" ]] || fail 'Forge installer did not create runtime/run.sh'

if [[ ! -f "$RUNTIME/user_jvm_args.txt" ]]; then
  cat > "$RUNTIME/user_jvm_args.txt" <<EOF
-Xms$SERVER_MIN_MEMORY
-Xmx$SERVER_MAX_MEMORY
-XX:+UseG1GC
-XX:+ParallelRefProcEnabled
-XX:MaxGCPauseMillis=200
EOF
fi

# Start with the bundled Isle of Berk map on loopback and a spare port.
if [[ ! -f "$RUNTIME/world/level.dat" ]]; then
  cp -a "$ROOT/pack/saves/Isle of Berk HTTYD Berk Island" "$RUNTIME/world"
  rm -f "$RUNTIME/world/session.lock"
fi
if [[ ! -s "$RUNTIME/server.properties" ]]; then
  cat > "$RUNTIME/server.properties" <<EOF
server-ip=127.0.0.1
server-port=$STAGE_PORT
level-name=world
online-mode=true
motd=Claws of Berk
max-players=20
view-distance=8
simulation-distance=6
enable-command-block=true
EOF
fi

# The existing server already accepted the same Mojang EULA; carry that
# acceptance forward without changing it if the old file confirms eula=true.
OLD_EULA="$HOME/minecraft/atfc/server/runtime/eula.txt"
if [[ ! -f "$RUNTIME/eula.txt" && -f "$OLD_EULA" ]] && grep -q '^eula=true$' "$OLD_EULA"; then
  cp "$OLD_EULA" "$RUNTIME/eula.txt"
fi
[[ -f "$RUNTIME/eula.txt" ]] || fail 'Review Mojang EULA and create server/runtime/eula.txt with eula=true before starting.'
grep -q '^eula=true$' "$RUNTIME/eula.txt" || fail 'Server EULA is not accepted in server/runtime/eula.txt'

UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$UNIT_DIR"
ln -sfn "$ROOT/server/minecraft-clawsofberk.service" "$UNIT_DIR/minecraft-clawsofberk.service"
systemctl --user daemon-reload
# On first install systemd has not loaded this unit yet, so reset-failed can
# return "Unit not loaded". Starting it below loads the unit normally.
systemctl --user reset-failed minecraft-clawsofberk.service >/dev/null 2>&1 || true

printf '%s\n' 'Starting test instance on 127.0.0.1:25566...'
systemctl --user start minecraft-clawsofberk.service
printf '%s\n' 'The old ATFC service remains running. Check the test instance with:'
printf '%s\n' '  systemctl --user status minecraft-clawsofberk.service'
printf '%s\n' '  journalctl --user -u minecraft-clawsofberk.service -f'
