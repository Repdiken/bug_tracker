from rest_framework.permissions import BasePermission
from projects.models import Project
from .models import IssueAssignee, Comment


class IsProjectContributor(BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get("project_id")

        return Project.objects.filter(
            id=project_id, contributors__user=request.user
        ).exists()


class IsIssueAssignee(BasePermission):
    def has_permission(self, request, view):
        issue_id = view.kwargs.get("issue_id")

        return IssueAssignee.objects.filter(
            issue_id=issue_id,
            user=request.user,
            is_deleted=False,
        ).exists()


class IsCommentOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


#   request
#     │
#     ▼
# has_permission()
#     │
#     ▼
# get_object()
#     │
#     ▼
# has_object_permission()
#     │
#     ▼
# View executes
