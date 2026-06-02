from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "candidate_name",
        "ai_score",
        "created_by",
        "created_at",
    )

    list_filter = (
        "ai_score",
        "created_at",
        "created_by",
    )

    search_fields = (
        "candidate_name",
        "resume",
        "job_description",
        "created_by__username",
        "created_by__email",
    )
