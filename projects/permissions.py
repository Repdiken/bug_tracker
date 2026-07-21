from rest_framework.permissions import BasePermission
from .models import Project, Contributor


class IsProjectOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "owner"):
            project = obj
        elif hasattr(obj, "project"):
            project = obj.project
        elif hasattr(obj, "issue"):
            project = obj.issue.project
        else:
            return False

        return project.owner == request.user

    def has_permission(self, request, view):
        project_id = view.kwargs.get("project_id")
        return Project.objects.filter(owner=request.user, id=project_id).exists()


class IsProjectAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):

        if hasattr(obj, "owner"):
            project = obj  # Project

        elif hasattr(obj, "project"):
            project = obj.project  # Contributor, Issue

        elif hasattr(obj, "issue"):
            project = obj.issue.project  # Comment

        else:
            return False

        return project.contributors.filter(
            user=request.user,
            role="admin",
            is_deleted=False,
        ).exists()

    def has_permission(self, request, view):
        project_id = view.kwargs.get("project_id")

        return Contributor.objects.filter(
            project_id=project_id,
            user=request.user,
            role="admin",
            is_deleted=False,
        ).exists()
