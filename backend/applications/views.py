import json

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .ai import extract_candidate_name, screen_candidate, stream_screen_candidate
from .models import Application
from .serializers import ApplicationSerializer, ScreenCandidateSerializer


class ScreenCandidateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # The starter used request.data['field'], which raises KeyError and returns a 500 for bad input.
        # A DRF serializer gives users a clear 400 response and validates blank strings before calling AI.
        serializer = ScreenCandidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # The starter prompt ignored the job description, producing an ungrounded score.
        # The AI service compares both inputs and asks for structured score/reason output.
        result = screen_candidate(data["job_description"], data["resume"])

        # The starter trusted raw model text as ai_score. We normalize decimals and words on the backend
        # so every frontend and API consumer receives the same numeric score.
        app = Application.objects.create(
            job_description=data["job_description"],
            resume=data["resume"],
            candidate_name=data.get("candidate_name") or extract_candidate_name(data["resume"]),
            ai_score=result.score,
            ai_reasons=result.reasons,
            created_by=request.user,
        )

        # The starter returned 200 after creating a row. 201 Created correctly describes this mutation.
        return Response(ApplicationSerializer(app).data, status=status.HTTP_201_CREATED)


class ScreenCandidateStreamView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ScreenCandidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        def events():
            stream = stream_screen_candidate(data["job_description"], data["resume"])
            parts = []
            result = None
            while True:
                try:
                    chunk = next(stream)
                    parts.append(chunk)
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                except StopIteration as stop:
                    result = stop.value
                    break

            app = Application.objects.create(
                job_description=data["job_description"],
                resume=data["resume"],
                candidate_name=data.get("candidate_name") or extract_candidate_name(data["resume"]),
                ai_score=result.score,
                ai_reasons=result.reasons,
                created_by=request.user,
            )
            yield f"data: {json.dumps({'type': 'complete', 'application': ApplicationSerializer(app).data})}\n\n"

        response = StreamingHttpResponse(events(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        return response


class ApplicationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Security fix: Application.objects.all() leaks every user's screenings.
        # Filtering by created_by enforces tenant isolation for authenticated HR users.
        queryset = Application.objects.filter(created_by=request.user)

        try:
            limit = min(int(request.query_params.get("limit", 50)), 100)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except ValueError:
            return Response({"detail": "limit and offset must be integers."}, status=status.HTTP_400_BAD_REQUEST)
        total = queryset.count()
        apps = queryset[offset : offset + limit]

        return Response(
            {
                "count": total,
                "limit": limit,
                "offset": offset,
                "results": ApplicationSerializer(apps, many=True).data,
            }
        )


class ApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        app = get_object_or_404(Application, pk=pk, created_by=request.user)
        return Response(ApplicationSerializer(app).data)
