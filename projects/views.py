from .models import Project, Contributor
from django.utils.timezone import now
from rest_framework.decorators import api_view, permission_classes
from .serializers import (
    ProjectCreateSerializer,
    ProjectListSerializer,
    ProjectDetailSerializer,
    ContributorCreateUpdateSerializer,
    ContributorListSerializer,
)
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .permissions import IsProjectOwner, IsProjectAdmin
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView


class ProjectListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectCreateSerializer
        return ProjectListSerializer

    def get_queryset(self):
        return Project.objects.filter(
            contributors__user=self.request.user,
            is_deleted=False,
        ).distinct()  # Give me unique projects where the current user appears in the contributors table


class ProjectDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectDetailSerializer
    # lookup_url_kwarg is used when generic views retrieve a single object, such as RetrieveAPIView or RetrieveUpdateDestroyAPIView
    lookup_url_kwarg = "project_id"

    def get_queryset(self):
        return Project.objects.filter(
            contributors__user=self.request.user,
            is_deleted=False,
        ).distinct()

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [IsAuthenticated]
        elif self.request.method == "PATCH":
            permission_classes = [IsAuthenticated, IsProjectOwner | IsProjectAdmin]
        elif self.request.method == "DELETE":
            permission_classes = [IsAuthenticated, IsProjectOwner]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]


class ContributorListCreateView(ListCreateAPIView):

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsProjectOwner | IsProjectAdmin]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ContributorListSerializer
        return ContributorCreateUpdateSerializer

    def get_queryset(self):
        return Contributor.objects.filter(
            project_id=self.kwargs["project_id"],
            project__contributors__user=self.request.user,
            project__contributors__is_deleted=False,
            is_deleted=False,
        ).distinct()


class ContributorDetailUpdateDeleteViews(RetrieveUpdateDestroyAPIView):
    lookup_url_kwarg = "contributor_id"

    def get_queryset(self):
        return Contributor.objects.filter(
            project_id=self.kwargs["project_id"],
            project__contributors__user=self.request.user,
            project__contributors__is_deleted=False,
            is_deleted=False,
        )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ContributorListSerializer
        return ContributorCreateUpdateSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [IsAuthenticated]
        elif self.request.method == "PATCH":
            permission_classes = [IsAuthenticated, IsProjectOwner]
        elif self.request.method == "DELETE":
            permission_classes = [IsAuthenticated, IsProjectOwner | IsProjectAdmin]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
