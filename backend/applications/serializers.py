from rest_framework import serializers

from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = [
            "id",
            "job_description",
            "resume",
            "candidate_name",
            "ai_score",
            "ai_reasons",
            "created_at",
        ]
        read_only_fields = ["id", "ai_score", "ai_reasons", "created_at"]


class ScreenCandidateSerializer(serializers.Serializer):
    job_description = serializers.CharField(trim_whitespace=True)
    resume = serializers.CharField(trim_whitespace=True)
    candidate_name = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)

    def validate(self, attrs):
        if not attrs["job_description"]:
            raise serializers.ValidationError({"job_description": "Job description is required."})
        if not attrs["resume"]:
            raise serializers.ValidationError({"resume": "Resume is required."})
        return attrs
