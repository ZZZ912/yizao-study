from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from provenance.models import ContentProvenance
from questions.models import Question, QuestionVersion


class Command(BaseCommand):
    help = "Explicitly publish a manually reviewed list of imported question external IDs."

    def add_arguments(self, parser):
        parser.add_argument("path", help="UTF-8 text file with one external_id per line.")
        parser.add_argument("--commit", action="store_true")

    def handle(self, *args, **options):
        path = Path(options["path"]).resolve()
        if not path.is_file():
            raise CommandError(f"Review list not found: {path}")
        external_ids = [
            line.strip().lower()
            for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        if not external_ids or len(external_ids) != len(set(external_ids)):
            raise CommandError("Review list must contain unique external IDs.")

        questions = {
            question.external_id: question
            for question in Question.objects.filter(external_id__in=external_ids)
            .select_related("current_version")
            .prefetch_related("current_version__options")
        }
        failures = []
        for external_id in external_ids:
            question = questions.get(external_id)
            if not question or not question.current_version:
                failures.append(f"{external_id}: missing current version")
                continue
            version = question.current_version
            labels = {option.label for option in version.options.all()}
            answers = set(version.canonical_answer)
            if version.warnings:
                failures.append(f"{external_id}: unresolved warnings")
            if not version.analysis.strip():
                failures.append(f"{external_id}: missing analysis")
            if not answers or not answers.issubset(labels):
                failures.append(f"{external_id}: invalid answer labels")
            if question.question_type == Question.Type.SINGLE_CHOICE and len(answers) != 1:
                failures.append(f"{external_id}: single choice cardinality")
            if question.question_type == Question.Type.MULTIPLE_CHOICE and len(answers) < 2:
                failures.append(f"{external_id}: multiple choice cardinality")
            if not ContentProvenance.objects.filter(
                content_type="question_version", content_object_id=version.id
            ).exists():
                failures.append(f"{external_id}: missing provenance")
        if failures:
            raise CommandError("Publication gate failed:\n" + "\n".join(failures))

        self.stdout.write(f"reviewed_candidates={len(external_ids)}")
        if not options["commit"]:
            self.stdout.write("mode=dry-run\nNo publication state was changed.")
            return

        with transaction.atomic():
            for external_id in external_ids:
                question = questions[external_id]
                version = question.current_version
                version.review_status = QuestionVersion.ReviewStatus.REVIEWED
                version.save()
                version.review_status = QuestionVersion.ReviewStatus.PUBLISHED
                version.save()
                question.status = Question.Status.PUBLISHED
                question.save(update_fields=("status", "updated_at"))
        self.stdout.write(self.style.SUCCESS(f"mode=commit\npublished={len(external_ids)}"))
