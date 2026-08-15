from rest_framework.test import APIClient
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from issues.models import Issue, IssueAssignee, Comment
from projects.models import Project, Contributor

User = get_user_model()


class BaseProjectTestCase(TestCase):
    """Base class to establish common state for project views."""

    def setUp(self):
        self.client = APIClient()

        # 1. Setup Global Users
        self.owner = User.objects.create_user(
            username="owner_user", password="password123"
        )
        self.member = User.objects.create_user(
            username="member_user", password="password123"
        )
        self.outsider = User.objects.create_user(
            username="outsider_user", password="password123"
        )

        # 2. Setup Global Project
        self.project = Project.objects.create(
            name="Default Test Project",
            description="Reused across tests",
            owner=self.owner,
        )

        # 3. Setup Core Contributors
        Contributor.objects.create(project=self.project, user=self.owner, role="admin")
        self.member_contributor = Contributor.objects.create(
            project=self.project, user=self.member, role="member"
        )

        # 4. Setup Base URLs
        self.list_url = reverse("project-list")
        self.detail_url = reverse("project-detail", args=[self.project.id])

        # 5. Default Authentication
        self.client.force_authenticate(user=self.owner)


class TestProjectListCreateViews(BaseProjectTestCase):
    """Tests focused on collection operations (GET list, POST create)."""

    def test_project_list_GET(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_project_create_POST(self):
        payload = {"name": "Test Project"}
        response = self.client.post(self.list_url, data=payload)
        self.assertEqual(response.status_code, 201)

    def test_project_limit_enforced_at_20(self):
        # Populate the database with exactly 20 projects for this user
        projects_to_create = [
            Project(
                name=f"Project {i}",
                description="Filling up the quota",
                owner=self.owner,
            )
            for i in range(19)
        ]
        Project.objects.bulk_create(projects_to_create)

        # Verify the setup was successful
        self.assertEqual(Project.objects.filter(owner=self.owner).count(), 20)

        # Attempt to create the 21st project via a POST request
        payload = {
            "name": "The 21st Project",
            "description": "This should be blocked by the API.",
        }
        response = self.client.post(self.list_url, data=payload)
        self.assertEqual(response.status_code, 400)

        # Verify the database still strictly contains only 20 projects
        self.assertEqual(Project.objects.filter(owner=self.owner).count(), 20)


class TestProjectDetailViews(BaseProjectTestCase):
    """Tests focused on individual project record operations and data isolation."""

    def test_project_detail_GET(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

    def test_project_update_PATCH(self):
        payload = {"name": "Updated Project Name"}
        response = self.client.patch(self.detail_url, data=payload)
        self.assertEqual(response.status_code, 200)

        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Updated Project Name")

    def test_project_delete_DELETE(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)

        self.project.refresh_from_db()
        self.assertTrue(self.project.is_deleted)

    def test_data_isolation_404(self):
        """Test that non-contributors receive a 404 when accessing a project."""
        self.client.force_authenticate(user=self.outsider)

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 404)

    def test_cascading_soft_delete(self):
        """Test that deleting a project soft-deletes its related models."""
        # Setup related objects using the member established in the base class
        issue = Issue.objects.create(
            project=self.project, creator=self.owner, name="Test Bug"
        )
        comment = Comment.objects.create(
            author=self.member, issue=issue, description="Test Comment"
        )
        assignee = IssueAssignee.objects.create(user=self.member, issue=issue)

        # Delete the project
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)

        # Verify project is soft-deleted
        self.project.refresh_from_db()
        self.assertTrue(self.project.is_deleted)
        self.assertIsNotNone(self.project.deleted_at)

        # Verify cascading soft-delete on related objects
        self.member_contributor.refresh_from_db()
        self.assertTrue(self.member_contributor.is_deleted)

        issue.refresh_from_db()
        self.assertTrue(issue.is_deleted)

        comment.refresh_from_db()
        self.assertTrue(comment.is_deleted)

        assignee.refresh_from_db()
        self.assertTrue(assignee.is_deleted)


class TestProjectOwnershipTransfer(BaseProjectTestCase):
    """Tests focused on the custom ownership transfer endpoint."""

    def setUp(self):
        super().setUp()
        self.transfer_url = reverse(
            "project-transfer-ownership", args=[self.project.id]
        )

    def test_successful_ownership_transfer(self):
        """Test that the owner can transfer ownership to an active contributor."""
        payload = {"new_owner": self.member.id}
        response = self.client.post(self.transfer_url, data=payload)

        self.assertEqual(response.status_code, 200)

        # Verify the project's owner field was updated
        self.project.refresh_from_db()
        self.assertEqual(self.project.owner, self.member)

        # Verify the new owner was upgraded to an admin role in the contributors table
        self.member_contributor.refresh_from_db()
        self.assertEqual(self.member_contributor.role, "admin")

    def test_outsider_cannot_become_owner(self):
        """Test that transferring ownership to a non-contributor fails validation."""
        payload = {"new_owner": self.outsider.id}
        response = self.client.post(self.transfer_url, data=payload)

        # Should fail serializer validation because the outsider is not in the dynamic queryset
        self.assertEqual(response.status_code, 400)
        self.assertIn("new_owner", response.data)

        # Verify the project's owner field did not change
        self.project.refresh_from_db()
        self.assertEqual(self.project.owner, self.owner)

    def test_only_owner_can_transfer_ownership(self):
        """Test that a regular member or admin cannot access the transfer endpoint."""
        self.client.force_authenticate(user=self.member)
        payload = {"new_owner": self.member.id}

        response = self.client.post(self.transfer_url, data=payload)

        # Should fail the IsProjectOwner permission check
        self.assertEqual(response.status_code, 403)

        # Verify the project's owner field did NOT change
        self.project.refresh_from_db()
        self.assertEqual(self.project.owner, self.owner)


class TestLeaveProjectView(BaseProjectTestCase):
    """Tests focused on the custom leave project endpoint."""

    def setUp(self):
        super().setUp()
        # Create a related issue to ensure it isn't deleted when the member leaves
        self.member_issue = Issue.objects.create(
            project=self.project, creator=self.member, name="Member's Issue"
        )
        self.leave_url = reverse("project-leave", args=[self.project.id])

    def test_member_can_leave_project(self):
        """Test that a standard member can successfully leave the project."""
        self.client.force_authenticate(user=self.member)

        response = self.client.post(self.leave_url)
        self.assertEqual(response.status_code, 200)

        # Verify the member's contributor record was soft-deleted
        self.member_contributor.refresh_from_db()
        self.assertTrue(self.member_contributor.is_deleted)
        self.assertIsNotNone(self.member_contributor.deleted_at)

        # Verify the issue they created still exists and is not deleted
        self.member_issue.refresh_from_db()
        self.assertFalse(self.member_issue.is_deleted)

    def test_owner_cannot_leave_project(self):
        """Test that the project owner is blocked from leaving."""
        response = self.client.post(self.leave_url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["detail"],
            "Project owners cannot leave their own projects. You must transfer ownership or delete the project.",
        )

        # Verify the owner's contributor record is still active
        owner_contributor = Contributor.objects.get(
            project=self.project, user=self.owner
        )
        self.assertFalse(owner_contributor.is_deleted)

    def test_non_contributor_cannot_leave(self):
        """Test that an outsider gets a 403 Forbidden when trying to leave."""
        self.client.force_authenticate(user=self.outsider)

        response = self.client.post(self.leave_url)

        # Denied by IsProjectContributor
        self.assertEqual(response.status_code, 403)
