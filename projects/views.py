from .models import Project, Contributor
from .serializers import (
    ProjectCreateSerializer,
    ProjectListSerializer,
    ProjectDetailSerializer,
    ContributorCreateUpdateSerializer,
    ContributorListSerializer,
)
from rest_framework.permissions import IsAuthenticated
from .permissions import IsProjectOwner, IsProjectAdmin, CanDeleteContributor
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.utils.timezone import now


class ProjectListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProjectCreateSerializer
        return ProjectListSerializer

    def get_queryset(self):
        return Project.objects.filter(
            Q(contributors__user=self.request.user) | Q(owner=self.request.user),
            is_deleted=False,
        ).distinct()


class ProjectDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectDetailSerializer
    # lookup_url_kwarg is used when generic views retrieve a single object, such as RetrieveAPIView or RetrieveUpdateDestroyAPIView
    lookup_url_kwarg = "project_id"

    def get_queryset(self):
        return Project.objects.filter(
            Q(contributors__user=self.request.user) | Q(owner=self.request.user),
            is_deleted=False,
        ).distinct()

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [IsAuthenticated]
        elif self.request.method in ["PATCH", "PUT"]:
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

    def perform_create(self, serializer):
        project = get_object_or_404(
            Project, pk=self.kwargs["project_id"], is_deleted=False
        )
        role = serializer.validated_data.get("role", "member")

        # If trying to add an admin, restrict to project owner
        if role == "admin" and project.owner != self.request.user:
            raise PermissionDenied("Only the project owner can add administrators.")

        serializer.save(project=project)


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

        elif self.request.method in ["PUT", "PATCH"]:
            permission_classes = [
                IsAuthenticated,
                IsProjectOwner,
            ]

        elif self.request.method == "DELETE":
            permission_classes = [
                IsAuthenticated,
                CanDeleteContributor,
            ]

        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = now()
        instance.save(update_fields=["is_deleted", "deleted_at"])
