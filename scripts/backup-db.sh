#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(CDPATH='' cd -- "$script_dir/.." && pwd)"
backup_root="${BACKUP_DIR:-$repo_root/backups}"
env_file="${ENV_FILE:-$repo_root/.env}"
compose_file="${COMPOSE_FILE:-$repo_root/docker-compose.prod.yml}"
backup_kind="${BACKUP_KIND:-daily}"
daily_keep="${BACKUP_DAILY_KEEP:-7}"
weekly_keep="${BACKUP_WEEKLY_KEEP:-4}"
safety_keep="${BACKUP_SAFETY_KEEP:-3}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive_name="yizao-study-${timestamp}.sql.gz"

for value_name in BACKUP_DAILY_KEEP BACKUP_WEEKLY_KEEP BACKUP_SAFETY_KEEP; do
    value="${!value_name:-}"
    if [[ -n "$value" ]] && ! [[ "$value" =~ ^[1-9][0-9]*$ ]]; then
        echo "$value_name must be a positive integer." >&2
        exit 1
    fi
done

if [[ ! -f "$env_file" ]]; then
    echo "Environment file not found: $env_file" >&2
    exit 1
fi

if [[ ! -f "$compose_file" ]]; then
    echo "Compose file not found: $compose_file" >&2
    exit 1
fi

case "$backup_kind" in
    daily | weekly | safety) ;;
    *)
        echo "BACKUP_KIND must be daily, weekly, or safety." >&2
        exit 1
        ;;
esac

compose=(
    docker compose
    --project-directory "$repo_root"
    --env-file "$env_file"
    --file "$compose_file"
)
if [[ -n "${COMPOSE_PROJECT_NAME:-}" ]]; then
    compose+=(--project-name "$COMPOSE_PROJECT_NAME")
fi

prune_backups() {
    local directory="$1"
    local keep_count="$2"
    local archives=()
    local index

    mapfile -t archives < <(
        find "$directory" -maxdepth 1 -type f -name 'yizao-study-*.sql.gz' \
            -printf '%T@ %p\n' | sort -rn | cut -d' ' -f2-
    )
    for ((index = keep_count; index < ${#archives[@]}; index++)); do
        rm -f -- "${archives[$index]}" "${archives[$index]}.sha256"
    done
}

create_backup() {
    local target_dir="$1"
    local temporary_archive="$target_dir/.${archive_name}.tmp"
    local final_archive="$target_dir/$archive_name"

    mkdir -p -- "$target_dir"
    chmod 0700 "$target_dir"

    # shellcheck disable=SC2329 # Invoked indirectly by the RETURN trap.
    cleanup_temporary() {
        rm -f -- "$temporary_archive"
    }
    trap cleanup_temporary RETURN

    # Container-side variables intentionally expand inside `sh -c`.
    # shellcheck disable=SC2016
    "${compose[@]}" exec -T db sh -c \
        'pg_dump --clean --if-exists --no-owner --no-privileges --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
        | gzip -9 > "$temporary_archive"

    test -s "$temporary_archive"
    gzip --test "$temporary_archive"
    chmod 0600 "$temporary_archive"
    mv -- "$temporary_archive" "$final_archive"

    (
        cd -- "$target_dir"
        sha256sum "$archive_name" > "$archive_name.sha256"
        chmod 0600 "$archive_name.sha256"
    )
    printf '%s\n' "$final_archive"
}

target_dir="$backup_root/$backup_kind"
final_archive="$(create_backup "$target_dir")"

case "$backup_kind" in
    daily)
        prune_backups "$target_dir" "$daily_keep"
        if [[ "${BACKUP_FORCE_WEEKLY:-false}" == "true" || "$(date -u +%u)" == "7" ]]; then
            weekly_dir="$backup_root/weekly"
            mkdir -p -- "$weekly_dir"
            chmod 0700 "$weekly_dir"
            cp -- "$final_archive" "$weekly_dir/$archive_name"
            cp -- "$final_archive.sha256" "$weekly_dir/$archive_name.sha256"
            prune_backups "$weekly_dir" "$weekly_keep"
        fi
        ;;
    weekly) prune_backups "$target_dir" "$weekly_keep" ;;
    safety) prune_backups "$target_dir" "$safety_keep" ;;
esac

echo "Backup created: $final_archive"
echo "Checksum: $final_archive.sha256"
echo "BACKUP_ARCHIVE=$final_archive"
