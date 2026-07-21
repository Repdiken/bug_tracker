from rest_framework import serializers
from .models import Issue, Comment, IssueAssignee
from users.models import User
from django.urls import reverse
from projects.models import Contributor


class IssueListSerializer(serializers.ModelSerializer):
    issue_url = serializers.SerializerMethodField()

    class Meta:
        model = Issue
        fields = ["issue_url", "name", "priority"]

    def get_issue_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(
            reverse("issue-detail", args=[obj.project_id, obj.id])
        )


class IssueDetailSerializer(serializers.ModelSerializer):
    assignee_page_url = serializers.SerializerMethodField()
    comment_page_url = serializers.SerializerMethodField()
    creator = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Issue
        fields = [
            "comment_page_url",
            "assignee_page_url",
            "name",
            "priority",
            "creator",
            "description",
            "deadline",
        ]

    def get_comment_page_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(
            reverse("issue_comments", args=[obj.project_id, obj.id])
        )

    def get_assignee_page_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(
            reverse("issue-assignees", args=[obj.project_id, obj.id])
        )


class IssueCreateSerializer(serializers.ModelSerializer):
    creator = serializers.PrimaryKeyRelatedField(read_only=True)
    project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Issue
        fields = ["name", "priority", "description", "deadline", "creator", "project"]
        extra_kwargs = {"deadline": {"required": False}}


class CommentListSerializer(serializers.ModelSerializer):
    comment_page_url = serializers.SerializerMethodField()
    author = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "comment_page_url",
            "author",
            "description",
            "created_at",
            "is_edited",
        ]

    def get_comment_page_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(
            reverse("comment_detail", args=[obj.issue.project_id, obj.issue_id, obj.id])
        )


class CommentDetailSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "author",
            "description",
            "created_at",
            "is_edited",
        ]


class CommentCreateSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ["author", "description"]


class IssueAssigneeListCreateSerializer(serializers.ModelSerializer):

    assignee_url = serializers.SerializerMethodField()

    class Meta:
        model = IssueAssignee
        fields = ["assignee_url", "user"]

    def get_assignee_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(
            reverse(
                "assignee_detail",
                args=[obj.issue.project_id, obj.issue_id, obj.id],
            )
        )

    def validate(self, attrs):
        issue = self.context["issue"]
        user = attrs["user"]

        is_contributor = Contributor.objects.filter(
            project=issue.project, user=user, is_deleted=False
        ).exists()

        if not is_contributor:
            raise serializers.ValidationError(
                "This user is not a contributor to this project."
            )

        return attrs

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        issue = self.context.get("issue")
        if issue:
            self.fields["user"].queryset = User.objects.filter(
                contributions__project=issue.project,
                contributions__is_deleted=False,
            ).distinct()


class IssueAssigneeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssueAssignee
        fields = ["user"]
