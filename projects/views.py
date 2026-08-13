from .models import Project, Contributor
from issues.models import Issue

from .serializers import (
    ProjectCreateSerializer,
    ProjectListSerializer,
    ProjectDetailSerializer,
    ContributorCreateUpdateSerializer,
    ContributorListSerializer,
    ProjectOwnershipTransferSerializer,
)
from rest_framework.permissions import IsAuthenticated
from .permissions import (
    IsProjectOwner,
    IsProjectAdmin,
    CanDeleteContributor,
    IsProjectContributor,
)

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    GenericAPIView,
)
from rest_framework.views import APIView

from django.db.models import Prefetch, Q

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
        active_contributors = Contributor.objects.filter(is_deleted=False)
        active_issues = Issue.objects.filter(is_deleted=False)

        return (
            Project.objects.filter(
                Q(contributors__user=self.request.user) | Q(owner=self.request.user),
                is_deleted=False,
            )
            .prefetch_related(
                Prefetch("contributors", queryset=active_contributors),
                Prefetch("issues", queryset=active_issues),
            )
            .distinct()
            .order_by("-created_at")
        )

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [IsAuthenticated]
        elif self.request.method in ["PATCH", "PUT"]:
            permission_classes = [IsAuthenticated, IsProjectOwner | IsProjectAdmin]
        else:
            permission_classes = [IsAuthenticated, IsProjectOwner]

        return [permission() for permission in permission_classes]


class ProjectOwnershipTransferView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsProjectOwner]
    serializer_class = ProjectOwnershipTransferSerializer

    def post(self, request, project_id):
        # 1. Fetch the project and verify ownership permissions
        project = get_object_or_404(Project, pk=project_id, is_deleted=False)
        # has_object_permission for every permission class assigned at the top
        self.check_object_permissions(request, project)

        # 2. Validate the payload using our new serializer
        serializer = ProjectOwnershipTransferSerializer(
            data=request.data, context={"view": self}
        )  # Send the context o the serializer to give it access to data outside the model fields
        # such as the currently logged-in user, URL parameters, or request headers
        serializer.is_valid(raise_exception=True)
        new_owner = serializer.validated_data["new_owner"]

        # Prevent transferring to themselves
        if new_owner == project.owner:
            return Response(
                {"detail": "You are already the owner of this project."},
                status=HTTP_400_BAD_REQUEST,
            )

        # 3. Ensure the new owner has admin privileges in the contributors table
        Contributor.objects.filter(
            project=project, user=new_owner, is_deleted=False
        ).update(role="admin")

        # 4. Transfer ownership
        project.owner = new_owner
        project.save(update_fields=["owner"])

        return Response(
            {"detail": f"Ownership successfully transferred to {new_owner.username}."},
            status=HTTP_200_OK,
        )


class ContributorListCreateView(ListCreateAPIView):

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [
                IsAuthenticated,
                IsProjectContributor | IsProjectOwner,
            ]
        else:
            permission_classes = [IsAuthenticated, IsProjectOwner | IsProjectAdmin]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ContributorListSerializer
        return ContributorCreateUpdateSerializer

    def get_queryset(self):
        return (
            Contributor.objects.filter(
                Q(project__owner=self.request.user)
                | Q(
                    project__contributors__user=self.request.user,
                    project__contributors__is_deleted=False,
                ),
                project_id=self.kwargs["project_id"],
                is_deleted=False,
            )
            .distinct()
            .order_by("-created_at")
        )

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
        return (
            Contributor.objects.filter(
                Q(project__owner=self.request.user)
                | Q(
                    project__contributors__user=self.request.user,
                    project__contributors__is_deleted=False,
                ),
                project_id=self.kwargs["project_id"],
                is_deleted=False,
            )
            .distinct()
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ContributorListSerializer
        return ContributorCreateUpdateSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [
                IsAuthenticated,
                IsProjectContributor | IsProjectOwner,
            ]

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
