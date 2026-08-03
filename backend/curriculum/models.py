import uuid

from django.db import models
from django.db.models.functions import Lower


class Subject(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.SlugField(max_length=60)
    title = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "curriculum_subject"
        ordering = ("code",)
        constraints = [
            models.UniqueConstraint(Lower("code"), name="subject_code_ci_uq"),
        ]

    def save(self, *args, **kwargs):
        self.code = self.code.strip().lower()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class Chapter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="chapters")
    number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=160)

    class Meta:
        db_table = "curriculum_chapter"
        ordering = ("subject", "number")
        constraints = [
            models.UniqueConstraint(fields=("subject", "number"), name="chapter_subject_number_uq")
        ]

    def __str__(self) -> str:
        return f"{self.number}. {self.title}"


class Section(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chapter = models.ForeignKey(Chapter, on_delete=models.PROTECT, related_name="sections")
    number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=180)

    class Meta:
        db_table = "curriculum_section"
        ordering = ("chapter", "number")
        constraints = [
            models.UniqueConstraint(fields=("chapter", "number"), name="section_chapter_number_uq")
        ]

    def __str__(self) -> str:
        return f"{self.chapter.number}.{self.number} {self.title}"
