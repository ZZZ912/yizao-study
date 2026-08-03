#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(CDPATH='' cd -- "$script_dir/.." && pwd)"
backup_dir="${BACKUP_DIR:-$repo_root/backups}"
retention_days="${BACKUP_RETENTION_DAYS:-14}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive_name="yizao-study-${timestamp}.sql.gz"
temporary_archive="$backup_dir/.${archive_name}.tmp"
final_archive="$backup_dir/$archive_name"

if ! [[ "$retention_days" =~ ^[0-9]+$ ]]; then
    echo "BACKUP_RETENTION_DAYS must be a non-negative integer." >&2
    exit 1
fi

mkdir -p -- "$backup_dir"
chmod 0700 "$backup_dir"

cleanup() {
    rm -f -- "$temporary_archive"
}
trap cleanup EXIT

docker compose \
    --project-directory "$repo_root" \
    --env-file "$repo_root/.env" \
    --file "$repo_root/docker-compose.prod.yml" \
    exec -T db sh -c \
    'pg_dump --clean --if-exists --no-owner --no-privileges --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
    | gzip -9 > "$temporary_archive"

test -s "$temporary_archive"
chmod 0600 "$temporary_archive"
mv -- "$temporary_archive" "$final_archive"

(
    cd -- "$backup_dir"
    sha256sum "$archive_name" > "$archive_name.sha256"
    chmod 0600 "$archive_name.sha256"
)

find "$backup_dir" -maxdepth 1 -type f \
    \( -name 'yizao-study-*.sql.gz' -o -name 'yizao-study-*.sql.gz.sha256' \) \
    -mtime "+$retention_days" -delete

echo "Backup created: $final_archive"
echo "Checksum: $final_archive.sha256"
