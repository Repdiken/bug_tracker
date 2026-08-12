from rest_framework.permissions import BasePermission
from .models import Project, Contributor
from django.db.models import Q


class IsProjectContributor(BasePermission):
    def has_permission(self, request, view):
        project_id = view.kwargs.get("project_id")

        return Project.objects.filter(
            Q(id=project_id)
            & (
                Q(owner=request.user)
                | Q(contributors__user=request.user, contributors__is_deleted=False)
            )
        ).exists()


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


class CanDeleteContributor(BasePermission):
    def has_object_permission(self, request, view, obj):
        project = obj.project

        # Nobody can delete themselves
        if obj.user == request.user:
            return False

        # Owner can delete any other contributor
        if project.owner == request.user:
            return True

        # Admins cannot delete other admins
        if obj.role == "admin":
            return False

        # Admin can delete regular members
        return project.contributors.filter(
            user=request.user,
            role="admin",
            is_deleted=False,
        ).exists()
