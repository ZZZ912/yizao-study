import json

from django.core.management.base import BaseCommand, CommandError

from provenance.ingestion import terminal_summary, validate_jsonl, write_report


class Command(BaseCommand):
    help = "Validate a private question JSONL file without writing content to the database."

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument("--report", help="Write the machine-readable report to this path.")

    def handle(self, *args, **options):
        try:
            result = validate_jsonl(options["path"])
        except (FileNotFoundError, UnicodeDecodeError) as exc:
            raise CommandError(str(exc)) from exc

        report_name = f"validate-{result.source_checksum[:16]}.json"
        report_path = write_report(result.report, options["report"], report_name)
        self.stdout.write(terminal_summary(result.report))
        self.stdout.write(f"report={report_path}")
        self.stdout.write(
            "report_json=" + json.dumps(result.report, ensure_ascii=False, separators=(",", ":"))
        )

        if result.has_errors:
            for issue in result.report["issues"]:
                for error in issue["errors"]:
                    self.stderr.write(
                        f"line={issue['line_number']} code={error['code']} path={error['path']} "
                        f"message={error['message']}"
                    )
            raise CommandError(
                f"Validation failed for {result.report['error_count']} JSONL record(s)."
            )
