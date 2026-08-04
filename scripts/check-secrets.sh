#!/usr/bin/env bash
set -Eeuo pipefail

forbidden_files="$(
    git ls-files \
        | grep -E '(^|/)(\.env($|\.)|[^/]+\.(pem|key|p12|pfx)$|id_rsa$|id_ed25519$)' \
        | grep -vE '(^|/)\.env\.example$' \
        || true
)"

private_content_files="$(
    git ls-files \
        | grep -Ei '(^|/)(private-data|source-materials|extracted-content|import-reports/private)/|section_questions_raw\.jsonl$|\.(pdf|zip)$|\.(private|commercial)\.jsonl$' \
        || true
)"

if [[ -n "$forbidden_files" ]]; then
    echo "Forbidden secret-bearing file names are tracked:" >&2
    echo "$forbidden_files" >&2
    exit 1
fi

if [[ -n "$private_content_files" ]]; then
    echo "Private or commercial content files are tracked:" >&2
    echo "$private_content_files" >&2
    exit 1
fi

if git grep -nEI \
    '(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36,})' \
    -- . ':!scripts/check-secrets.sh'; then
    echo "Potential credential material found in tracked files." >&2
    exit 1
fi

echo "Tracked-file secret checks passed."
