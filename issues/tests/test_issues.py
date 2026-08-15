from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from projects.models import Project, Contributor
from issues.models import Issue, IssueAssignee

User = get_user_model()


class TestIssueVisibility(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Setup Users
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.assigned_member = User.objects.create_user(
            username="assigned_member", password="password123"
        )
        self.unassigned_member = User.objects.create_user(
            username="unassigned_member", password="password123"
        )

        # 2. Setup Project (Note: Owner is explicitly NOT created as a Contributor here)
        self.project = Project.objects.create(name="Test Project", owner=self.owner)

        # 3. Setup Contributors
        Contributor.objects.create(
            project=self.project, user=self.assigned_member, role="member"
        )
        Contributor.objects.create(
            project=self.project, user=self.unassigned_member, role="member"
        )

        # 4. Setup Issue & Assignment
        self.issue = Issue.objects.create(
            project=self.project, creator=self.owner, name="Visibility Issue"
        )
        IssueAssignee.objects.create(issue=self.issue, user=self.assigned_member)

        # 5. URLs
        self.issue_list_url = reverse("project-issues", args=[self.project.id])
        self.issue_detail_url = reverse(
            "issue-detail", args=[self.project.id, self.issue.id]
        )

    def test_owner_can_see_issue_without_assignment(self):
        """Test that the project owner sees the issue despite not being in the assignees or contributors table."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.issue_detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Visibility Issue")

    def test_assigned_member_can_see_issue(self):
        """Test that an active assignee can view the issue."""
        self.client.force_authenticate(user=self.assigned_member)
        response = self.client.get(self.issue_detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Visibility Issue")

    def test_unassigned_member_cannot_see_issue(self):
        """Test that a project contributor who is NOT assigned receives a 404 Not Found."""
        self.client.force_authenticate(user=self.unassigned_member)
        response = self.client.get(self.issue_detail_url)

        # 404 proves our get_queryset() filtering is completely isolating the data
        self.assertEqual(response.status_code, 404)


class TestIssueAssigneeCreation(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.admin = User.objects.create_user(username="admin", password="password123")
        self.member = User.objects.create_user(
            username="member", password="password123"
        )

        self.project = Project.objects.create(name="Assignee Test", owner=self.owner)

        # Setup Contributors
        Contributor.objects.create(project=self.project, user=self.admin, role="admin")
        Contributor.objects.create(
            project=self.project, user=self.member, role="member"
        )

        self.issue = Issue.objects.create(
            project=self.project, creator=self.owner, name="Test Bug"
        )

        self.assignee_url = reverse(
            "issue-assignees", args=[self.project.id, self.issue.id]
        )

    def test_owner_can_assign_member_to_issue(self):
        """Test that an owner can successfully assign a project contributor to an issue."""
        self.client.force_authenticate(user=self.owner)
        payload = {"user": self.member.id}

        response = self.client.post(self.assignee_url, data=payload)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            IssueAssignee.objects.filter(issue=self.issue, user=self.member).exists()
        )

    def test_admin_can_assign_member_to_issue(self):
        """Test that an admin can successfully assign a project contributor to an issue."""
        self.client.force_authenticate(user=self.admin)
        payload = {"user": self.member.id}

        response = self.client.post(self.assignee_url, data=payload)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            IssueAssignee.objects.filter(issue=self.issue, user=self.member).exists()
        )
