from django.db import models
from projects.models import Project
from users.models import User
from django.utils import timezone


class Issue(models.Model):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="issues"
    )
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    class PriorityChoice(models.TextChoices):
        URGENT = "urgent", "Urgent"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    priority = models.CharField(
        max_length=20, choices=PriorityChoice.choices, blank=True, null=True
    )

    class State(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        PAUSED = "paused", "Paused"
        ARCHIVED = "archived", "Archived"

    state = models.CharField(max_length=20, choices=State.choices, default=State.ACTIVE)

    deadline = models.DateTimeField(blank=True, null=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        timestamp = timezone.now()
        self.comments.update(is_deleted=True, deleted_at=timestamp)
        self.assignees.update(is_deleted=True, deleted_at=timestamp)
        self.is_deleted = True
        self.deleted_at = timestamp
        self.save(update_fields=["is_deleted", "deleted_at"])

    def __str__(self):
        return self.name


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="comments")

    description = models.TextField(blank=True)

    # function to handle editing
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.description


class IssueAssignee(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="issue_assignments"
    )

    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="assignees")

    created_at = models.DateTimeField(auto_now_add=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
