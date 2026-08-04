import json
import uuid

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from provenance.ingestion import (
    ContentValidationError,
    commit_import,
    dry_run_import,
    terminal_summary,
    validate_jsonl,
    write_report,
)


class Command(BaseCommand):
    help = "Dry-run or explicitly commit a private question JSONL import."

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument(
            "--dry-run", action="store_true", help="Validate and plan only (default)."
        )
        parser.add_argument(
            "--commit", action="store_true", help="Write the validated batch atomically."
        )
        parser.add_argument("--batch-id", help="Use this UUID for the committed import batch.")
        parser.add_argument("--report", help="Write the machine-readable report to this path.")

    def handle(self, *args, **options):
        if options["commit"] and options["dry_run"]:
            raise CommandError("Choose either --dry-run or --commit, not both.")
        if options["batch_id"] and not options["commit"]:
            raise CommandError("--batch-id requires --commit.")

        try:
            result = validate_jsonl(options["path"])
        except (FileNotFoundError, UnicodeDecodeError) as exc:
            raise CommandError(str(exc)) from exc

        if result.has_errors and options["commit"]:
            report_name = f"import-error-{result.source_checksum[:16]}.json"
            report_path = write_report(result.report, options["report"], report_name)
            self.stdout.write(terminal_summary(result.report))
            self.stdout.write(f"report={report_path}")
            for issue in result.report["issues"]:
                for error in issue["errors"]:
                    self.stderr.write(
                        f"line={issue['line_number']} code={error['code']} path={error['path']} "
                        f"message={error['message']}"
                    )
            raise CommandError("Import validation failed; no database content was written.")

        if result.has_errors:
            self.stderr.write(
                self.style.WARNING(
                    "Dry-run continues with valid records only; --commit would reject this batch."
                )
            )

        if options["commit"]:
            try:
                batch_id = uuid.UUID(options["batch_id"]) if options["batch_id"] else None
                batch, report = commit_import(result, batch_id=batch_id)
            except (ValueError, ValidationError, ContentValidationError) as exc:
                raise CommandError(str(exc)) from exc
            report_name = f"import-{batch.id}.json"
            mode = "commit"
        else:
            report = dry_run_import(result)
            report_name = f"dry-run-{result.source_checksum[:16]}.json"
            mode = "dry-run"

        report = {**report, "mode": mode}
        report_path = write_report(report, options["report"], report_name)
        self.stdout.write(terminal_summary(report))
        self.stdout.write(f"mode={mode}")
        self.stdout.write(f"report={report_path}")
        self.stdout.write(
            "report_json=" + json.dumps(report, ensure_ascii=False, separators=(",", ":"))
        )
