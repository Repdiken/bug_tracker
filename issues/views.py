from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from .models import Issue, Comment, IssueAssignee
from projects.models import Project
from .serializers import (
    IssueListSerializer,
    IssueDetailSerializer,
    IssueCreateSerializer,
    CommentListSerializer,
    CommentCreateSerializer,
    CommentDetailSerializer,
    IssueAssigneeListCreateSerializer,
    IssueAssigneeDetailSerializer,
)
from .permissions import IsProjectContributor, IsIssueAssignee, IsCommentOwner
from projects.permissions import IsProjectOwner, IsProjectAdmin
from rest_framework.permissions import IsAuthenticated

from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveDestroyAPIView,
)


class IssueListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsProjectAdmin | IsProjectOwner]

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [IsAuthenticated, IsProjectContributor]
        else:
            permission_classes = [IsAuthenticated, IsProjectAdmin | IsProjectOwner]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return IssueListSerializer
        else:
            return IssueCreateSerializer

    def get_queryset(self):
        return Issue.objects.filter(
            project_id=self.kwargs["project_id"], is_deleted=False
        )

    def perform_create(self, serializer):
        project = get_object_or_404(
            Project,
            pk=self.kwargs["project_id"],
            is_deleted=False,
        )
        serializer.save(
            project=project,
            creator=self.request.user,
        )


class IssueDetailUpdateDeleteView(RetrieveUpdateDestroyAPIView):

    def get_queryset(self):
        return Issue.objects.filter(
            project_id=self.kwargs["project_id"],
            is_deleted=False,
            project__contributors__user=self.request.user,
            project__contributors__is_deleted=False,
            project__is_deleted=False,
        )

    lookup_url_kwarg = "issue_id"
    serializer_class = IssueDetailSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsProjectAdmin | IsProjectOwner]
        return [permission() for permission in permission_classes]


class IssueAssagineeListCreateView(ListCreateAPIView):
    serializer_class = IssueAssigneeListCreateSerializer

    def get_queryset(self):
        return IssueAssignee.objects.filter(
            issue_id=self.kwargs["issue_id"], is_deleted=False
        )

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [IsAuthenticated, IsProjectContributor]
        else:
            permission_classes = [
                IsAuthenticated,
                IsProjectAdmin | IsProjectOwner,
            ]
        return [permission() for permission in permission_classes]

    def get_issue(self):
        return get_object_or_404(
            Issue,
            pk=self.kwargs["issue_id"],
            project_id=self.kwargs["project_id"],
            is_deleted=False,
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["issue"] = self.get_issue()
        return context

    def perform_create(self, serializer):
        serializer.save(issue=self.get_issue())


class IssueAssigneeDetailDeleteView(RetrieveDestroyAPIView):
    serializer_class = IssueAssigneeDetailSerializer
    lookup_url_kwarg = "assignee_id"

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = now()
        instance.save(update_fields=["is_deleted", "deleted_at"])

    def get_queryset(self):
        return IssueAssignee.objects.filter(
            issue_id=self.kwargs["issue_id"],
            is_deleted=False,
        )

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [IsAuthenticated, IsProjectContributor]
        else:
            permission_classes = [IsAuthenticated, IsProjectAdmin | IsProjectOwner]
        return [permission() for permission in permission_classes]


class CommentListCreateView(ListCreateAPIView):

    def get_queryset(self):
        return Comment.objects.filter(
            issue_id=self.kwargs["issue_id"],
            issue__project_id=self.kwargs["project_id"],
            is_deleted=False,
        )

    permission_classes = [IsAuthenticated, IsIssueAssignee]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CommentListSerializer
        else:
            return CommentCreateSerializer

    def perform_create(self, serializer):
        issue = get_object_or_404(
            Issue,
            pk=self.kwargs["issue_id"],
            project_id=self.kwargs["project_id"],
            is_deleted=False,
        )

        serializer.save(
            author=self.request.user,
            issue=issue,
        )


class CommentDetailUpdateDelete(RetrieveUpdateDestroyAPIView):

    lookup_url_kwarg = "comment_id"

    def get_queryset(self):
        return Comment.objects.filter(
            issue_id=self.kwargs["issue_id"],
            issue__project_id=self.kwargs["project_id"],
            is_deleted=False,
        )

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [IsAuthenticated, IsProjectContributor]
        elif self.request.method in ["PUT", "PATCH"]:
            permission_classes = [IsAuthenticated, IsCommentOwner]
        elif self.request.method == "DELETE":
            permission_classes = [
                IsAuthenticated,
                IsProjectAdmin | IsProjectOwner | IsCommentOwner,
            ]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CommentDetailSerializer
        else:
            return CommentCreateSerializer

    def perform_update(self, serializer):
        return serializer.save(is_edited=True, edited_at=now())

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.deleted_at = now()
        instance.save(update_fields=["is_deleted", "deleted_at"])
