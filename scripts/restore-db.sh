#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: RESTORE_CONFIRM=restore scripts/restore-db.sh <backup.sql.gz>" >&2
    exit 2
fi

if [[ "${RESTORE_CONFIRM:-}" != "restore" ]]; then
    echo "Restore replaces data. Set RESTORE_CONFIRM=restore to confirm." >&2
    exit 2
fi

script_dir="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(CDPATH='' cd -- "$script_dir/.." && pwd)"
env_file="${ENV_FILE:-$repo_root/.env}"
compose_file="${COMPOSE_FILE:-$repo_root/docker-compose.prod.yml}"
skip_app_control="${RESTORE_SKIP_APP_CONTROL:-false}"

if [[ ! -f "$1" ]]; then
    echo "Backup not found: $1" >&2
    exit 1
fi
archive="$(realpath -- "$1")"
archive_dir="$(dirname -- "$archive")"
archive_name="$(basename -- "$archive")"
checksum="$archive.sha256"

if [[ ! -f "$checksum" ]]; then
    echo "Checksum not found: $checksum" >&2
    exit 1
fi
if [[ ! -f "$env_file" ]]; then
    echo "Environment file not found: $env_file" >&2
    exit 1
fi
if [[ ! -f "$compose_file" ]]; then
    echo "Compose file not found: $compose_file" >&2
    exit 1
fi

compose=(
    docker compose
    --project-directory "$repo_root"
    --env-file "$env_file"
    --file "$compose_file"
)
if [[ -n "${COMPOSE_PROJECT_NAME:-}" ]]; then
    compose+=(--project-name "$COMPOSE_PROJECT_NAME")
fi

(
    cd -- "$archive_dir"
    sha256sum --check "${archive_name}.sha256"
)
gzip --test "$archive"

backend_stopped=false
restore_cleanup() {
    if [[ "$backend_stopped" == "true" ]]; then
        echo "Restarting backend after interrupted restore..." >&2
        "${compose[@]}" up --detach backend || true
    fi
}
trap restore_cleanup EXIT

if [[ "$skip_app_control" != "true" ]]; then
    echo "Stopping backend to prevent writes during restore..."
    "${compose[@]}" stop backend
    backend_stopped=true
fi

echo "Creating a pre-restore safety backup..."
BACKUP_KIND=safety \
    BACKUP_DIR="${BACKUP_DIR:-$repo_root/backups}" \
    ENV_FILE="$env_file" \
    COMPOSE_FILE="$compose_file" \
    COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-}" \
    "$script_dir/backup-db.sh"

echo "Restoring in a single database transaction..."
# Container-side variables intentionally expand inside `sh -c`.
# shellcheck disable=SC2016
gzip --decompress --stdout -- "$archive" \
    | "${compose[@]}" exec -T db sh -c \
        'psql --single-transaction --set ON_ERROR_STOP=1 --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"'

if [[ "$skip_app_control" != "true" ]]; then
    echo "Applying and checking Django migrations before resuming traffic..."
    "${compose[@]}" run --rm --no-deps --entrypoint python backend \
        manage.py migrate --noinput
    "${compose[@]}" run --rm --no-deps --entrypoint python backend \
        manage.py migrate --check

    "${compose[@]}" up --detach backend
    backend_stopped=false

    ready=false
    for _ in {1..12}; do
        if "${compose[@]}" exec -T backend python -c \
            "import urllib.request; request = urllib.request.Request('http://127.0.0.1:8000/api/health/ready/', headers={'X-Forwarded-Proto': 'https'}); urllib.request.urlopen(request, timeout=3)"; then
            ready=true
            break
        fi
        sleep 5
    done
    if [[ "$ready" != "true" ]]; then
        echo "Backend did not become ready after restore." >&2
        exit 1
    fi
fi

trap - EXIT
echo "Restore completed and verified from: $archive"
