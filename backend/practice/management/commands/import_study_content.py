import hashlib
import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from curriculum.models import Chapter, Section, Subject
from knowledge.models import KnowledgePoint, KnowledgeVersion


class BaseStudyContentError(Exception):
    pass


def validate_payload(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise BaseStudyContentError("Study content root must be an object.")
    subjects = payload.get("subjects")
    points = payload.get("knowledge_points")
    if not isinstance(subjects, list) or not isinstance(points, list):
        raise BaseStudyContentError("subjects and knowledge_points must be arrays.")
    for index, subject in enumerate(subjects, start=1):
        if not isinstance(subject, dict) or not subject.get("code") or not subject.get("title"):
            raise BaseStudyContentError(f"subjects[{index}] requires code and title.")
        if not isinstance(subject.get("chapters"), list):
            raise BaseStudyContentError(f"subjects[{index}].chapters must be an array.")
        for chapter in subject["chapters"]:
            if not isinstance(chapter.get("sections"), list):
                raise BaseStudyContentError("Each chapter requires a sections array.")
    for index, point in enumerate(points, start=1):
        required = {"subject_code", "chapter", "section", "code", "title", "summary", "blocks"}
        if not isinstance(point, dict) or not required.issubset(point):
            raise BaseStudyContentError(f"knowledge_points[{index}] is incomplete.")
        if not isinstance(point["blocks"], list):
            raise BaseStudyContentError(f"knowledge_points[{index}].blocks must be an array.")
        for block in point["blocks"]:
            if not isinstance(block, dict) or block.get("type") not in {
                "introduction",
                "markdown",
                "key_point",
                "formula",
                "example",
                "case",
                "warning",
                "comparison",
                "mnemonic",
                "inline_quiz",
                "summary",
            }:
                raise BaseStudyContentError(f"knowledge_points[{index}] has an invalid block.")
            if not isinstance(block.get("content"), str) or not block["content"].strip():
                raise BaseStudyContentError(f"knowledge_points[{index}] has an empty block.")
    return payload


class Command(BaseCommand):
    help = "Validate or explicitly import reviewed, original study summaries."

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument("--commit", action="store_true")

    def handle(self, *args, **options):
        path = Path(options["path"]).resolve()
        if not path.is_file():
            raise CommandError(f"Study content file not found: {path}")
        try:
            payload = validate_payload(json.loads(path.read_text(encoding="utf-8-sig")))
        except (json.JSONDecodeError, UnicodeDecodeError, BaseStudyContentError) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            f"subjects={len(payload['subjects'])}\nknowledge_points={len(payload['knowledge_points'])}"
        )
        if not options["commit"]:
            self.stdout.write("mode=dry-run\nNo database content was written.")
            return

        try:
            with transaction.atomic():
                section_map = {}
                for subject_data in payload["subjects"]:
                    subject, _ = Subject.objects.get_or_create(
                        code=subject_data["code"],
                        defaults={"title": subject_data["title"]},
                    )
                    if subject.title != subject_data["title"]:
                        subject.title = subject_data["title"]
                        subject.save(update_fields=("title",))
                    for chapter_data in subject_data["chapters"]:
                        chapter, _ = Chapter.objects.get_or_create(
                            subject=subject,
                            number=chapter_data["number"],
                            defaults={"title": chapter_data["title"]},
                        )
                        if chapter.title != chapter_data["title"]:
                            chapter.title = chapter_data["title"]
                            chapter.save(update_fields=("title",))
                        for section_data in chapter_data["sections"]:
                            section, _ = Section.objects.get_or_create(
                                chapter=chapter,
                                number=section_data["number"],
                                defaults={"title": section_data["title"]},
                            )
                            if section.title != section_data["title"]:
                                section.title = section_data["title"]
                                section.save(update_fields=("title",))
                            section_map[(subject.code, chapter.number, section.number)] = section

                created = versioned = skipped = 0
                for point_data in payload["knowledge_points"]:
                    key = (
                        point_data["subject_code"].lower(),
                        point_data["chapter"],
                        point_data["section"],
                    )
                    section = section_map.get(key)
                    if not section:
                        raise BaseStudyContentError(
                            f"Unknown curriculum location for {point_data['code']}."
                        )
                    point, was_created = KnowledgePoint.objects.get_or_create(
                        section=section,
                        code=point_data["code"],
                        defaults={
                            "title": point_data["title"],
                            "description": point_data["summary"],
                            "sort_order": point_data.get("sort_order", 0),
                        },
                    )
                    normalized = json.dumps(
                        {
                            "summary": point_data["summary"],
                            "blocks": point_data["blocks"],
                            "exam_edition": point_data.get("exam_edition", "2025大纲/2026考试"),
                            "source_type": point_data.get("source_type", "original_synthesis"),
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    checksum = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                    latest = point.versions.order_by("-version_number").first()
                    if latest and latest.content_checksum == checksum:
                        skipped += 1
                        continue
                    version = KnowledgeVersion(
                        knowledge_point=point,
                        version_number=(latest.version_number + 1 if latest else 1),
                        summary=point_data["summary"],
                        content_blocks=point_data["blocks"],
                        applicable_exam_edition=point_data.get("exam_edition", "2025大纲/2026考试"),
                        source_type=point_data.get("source_type", "original_synthesis"),
                        content_checksum=checksum,
                        review_status=KnowledgeVersion.ReviewStatus.PUBLISHED,
                    )
                    version.full_clean()
                    version.save()
                    KnowledgePoint.objects.filter(pk=point.pk).update(current_version=version)
                    if was_created:
                        created += 1
                    else:
                        versioned += 1
        except (BaseStudyContentError, ValidationError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"mode=commit\ncreated={created}\nversioned={versioned}\nskipped={skipped}"
            )
        )
