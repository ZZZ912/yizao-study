import uuid

from django.db import models
from django.db.models.functions import Lower

from curriculum.models import Section


class KnowledgePoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name="knowledge_points")
    code = models.SlugField(max_length=80)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "knowledge_point"
        ordering = ("section", "code")
        constraints = [
            models.UniqueConstraint(
                models.F("section"),
                Lower("code"),
                name="knowledge_section_code_ci_uq",
            )
        ]

    def save(self, *args, **kwargs):
        self.code = self.code.strip().lower()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title
