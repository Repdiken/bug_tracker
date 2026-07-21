from django.db import models
from users.models import User
from django.utils import timezone


class Project(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class State(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        ARCHIVED = "archived", "Archived"

    state = models.CharField(choices=State.choices, default=State.ACTIVE)

    def delete(self, *args, **kwargs):
        from issues.models import Comment, IssueAssignee

        timestamp = timezone.now()

        # Issues
        self.issues.update(is_deleted=True, deleted_at=timestamp)
        # Contributors
        self.contributors.update(is_deleted=True, deleted_at=timestamp)
        # Comments
        Comment.objects.filter(issue__project=self).update(
            is_deleted=True, deleted_at=timestamp
        )
        # Assignees
        IssueAssignee.objects.filter(issue__project=self).update(
            is_deleted=True, deleted_at=timestamp
        )
        # Project
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = timestamp
        self.save(update_fields=["is_deleted", "is_active", "deleted_at"])

    def __str__(self):
        return self.name


class Contributor(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="contributions"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="contributors"
    )

    class RoleOption(models.TextChoices):
        MEMBER = "member", "Member"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=20, choices=RoleOption.choices, default=RoleOption.MEMBER
    )

    created_at = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username  # self.user returns a whole user object, not a string

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "project"], name="unique_project_contributor"
            )
        ]
