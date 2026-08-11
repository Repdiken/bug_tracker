from rest_framework import serializers
from .models import Project, Contributor
from django.urls import reverse
from users.models import User
from issues.serializers import IssueListSerializer


class ProjectCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ["name", "description"]

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user

        # create project
        project = Project.objects.create(owner=user, **validated_data)

        # auto-add contributor as owner
        Contributor.objects.create(user=user, project=project, role="admin")

        return project


class ContributorListSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    url = serializers.SerializerMethodField()

    class Meta:
        model = Contributor
        fields = [
            "url",
            "user",
            "role",
        ]

    def get_url(self, obj):
        url = reverse("project-contributor-detail", args=[obj.project_id, obj.id])
        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(url)
        return url


class ProjectListSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ["url", "name", "description"]

    def get_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(reverse("project-detail", args=[obj.id]))


class ProjectDetailSerializer(serializers.ModelSerializer):
    contributors_page_url = serializers.SerializerMethodField()
    contributors = ContributorListSerializer(many=True, read_only=True)
    issues_page_url = serializers.SerializerMethodField()
    issues = IssueListSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "contributors_page_url",
            "contributors",
            "issues_page_url",
            "issues",
        ]

    def get_issues_page_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(reverse("project-issues", args=[obj.id]))

    def get_contributors_page_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(
            reverse("project-contributors", args=[obj.id])
        )


class ContributorCreateUpdateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()  # When someone sends a user ID, check inside THIS list of users to make sure it exists.
    )

    class Meta:
        model = Contributor
        fields = ["user", "role"]

    def validate(self, attrs):
        request = self.context.get("request")
        view = self.context.get("view")

        # Only validate duplicates during creation (POST requests)
        if request and request.method == "POST":
            project_id = view.kwargs.get("project_id")
            target_user = attrs.get("user")

            exists = Contributor.objects.filter(
                project_id=project_id, user=target_user, is_deleted=False
            ).exists()

            if exists:
                raise serializers.ValidationError(
                    {
                        "user": "This user is already an active contributor to this project."
                    }
                )
        return attrs
