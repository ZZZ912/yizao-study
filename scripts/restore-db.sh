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
archive="$(realpath -- "$1")"
archive_dir="$(dirname -- "$archive")"
archive_name="$(basename -- "$archive")"
checksum="$archive.sha256"

if [[ ! -f "$archive" ]]; then
    echo "Backup not found: $archive" >&2
    exit 1
fi

if [[ ! -f "$checksum" ]]; then
    echo "Checksum not found: $checksum" >&2
    exit 1
fi

(
    cd -- "$archive_dir"
    sha256sum --check "${archive_name}.sha256"
)

gzip --test "$archive"

gzip --decompress --stdout -- "$archive" \
    | docker compose \
        --project-directory "$repo_root" \
        --env-file "$repo_root/.env" \
        --file "$repo_root/docker-compose.prod.yml" \
        exec -T db sh -c \
        'psql --set ON_ERROR_STOP=1 --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"'

echo "Restore completed from: $archive"
