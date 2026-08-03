#!/usr/bin/env bash
set -Eeuo pipefail

script_dir="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(CDPATH='' cd -- "$script_dir/.." && pwd)"
drill_dir="$(mktemp -d)"
project_name="yizao-restore-drill-${GITHUB_RUN_ID:-$$}"
compose_file="$repo_root/deploy/docker-compose.restore-drill.yml"
env_file="$repo_root/.env.example"
compose=(
    docker compose
    --project-directory "$repo_root"
    --env-file "$env_file"
    --file "$compose_file"
    --project-name "$project_name"
)

cleanup() {
    "${compose[@]}" down --volumes --remove-orphans || true
    if [[ "$drill_dir" == "${TMPDIR:-/tmp}"/* || "$drill_dir" == /tmp/* ]]; then
        rm -rf -- "$drill_dir"
    fi
}
trap cleanup EXIT

"${compose[@]}" up --detach --wait db
"${compose[@]}" exec -T db psql --set ON_ERROR_STOP=1 \
    --username restore_drill --dbname restore_drill <<'SQL'
CREATE TABLE restore_probe (id integer PRIMARY KEY, value text NOT NULL);
INSERT INTO restore_probe (id, value) VALUES (1, 'before-backup');
SQL

BACKUP_DIR="$drill_dir" \
    BACKUP_KIND=daily \
    ENV_FILE="$env_file" \
    COMPOSE_FILE="$compose_file" \
    COMPOSE_PROJECT_NAME="$project_name" \
    "$script_dir/backup-db.sh"

archive="$(find "$drill_dir/daily" -maxdepth 1 -type f -name '*.sql.gz' -print -quit)"
test -n "$archive"

"${compose[@]}" exec -T db psql --set ON_ERROR_STOP=1 \
    --username restore_drill --dbname restore_drill \
    --command "UPDATE restore_probe SET value = 'after-backup' WHERE id = 1;"

RESTORE_CONFIRM=restore \
    RESTORE_SKIP_APP_CONTROL=true \
    BACKUP_DIR="$drill_dir" \
    ENV_FILE="$env_file" \
    COMPOSE_FILE="$compose_file" \
    COMPOSE_PROJECT_NAME="$project_name" \
    "$script_dir/restore-db.sh" "$archive"

restored_value="$(
    "${compose[@]}" exec -T db psql --tuples-only --no-align \
        --username restore_drill --dbname restore_drill \
        --command "SELECT value FROM restore_probe WHERE id = 1;"
)"
if [[ "$restored_value" != "before-backup" ]]; then
    echo "Restore drill failed: expected before-backup, got $restored_value" >&2
    exit 1
fi

echo "Backup and transactional restore drill passed."
