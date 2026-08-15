from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from projects.models import Project, Contributor
from issues.models import Issue, IssueAssignee, Comment

User = get_user_model()


class TestCommentPermissionsAndRetention(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Setup Users
        self.owner = User.objects.create_user(username="owner", password="password123")
        self.admin = User.objects.create_user(username="admin", password="password123")
        self.assignee = User.objects.create_user(
            username="assignee", password="password123"
        )

        # 2. Setup Project & Contributors
        self.project = Project.objects.create(
            name="Comment Test Project", owner=self.owner
        )
        Contributor.objects.create(project=self.project, user=self.admin, role="admin")
        Contributor.objects.create(
            project=self.project, user=self.assignee, role="member"
        )

        # 3. Setup Issue & Assignment
        self.issue = Issue.objects.create(
            project=self.project, creator=self.owner, name="Comment Issue"
        )
        self.assignee_record = IssueAssignee.objects.create(
            issue=self.issue, user=self.assignee
        )

        # 4. Setup Comments
        self.assignee_comment = Comment.objects.create(
            issue=self.issue, author=self.assignee, description="I am the assignee."
        )
        self.owner_comment = Comment.objects.create(
            issue=self.issue, author=self.owner, description="I am the owner."
        )

        # 5. URLs
        self.assignee_comment_url = reverse(
            "comment_detail",
            args=[self.project.id, self.issue.id, self.assignee_comment.id],
        )
        self.owner_comment_url = reverse(
            "comment_detail",
            args=[self.project.id, self.issue.id, self.owner_comment.id],
        )

    def test_owner_can_edit_own_comment_without_assignment(self):
        """Test the PUT/PATCH bitwise fix: Owner can edit their comment without being an assignee."""
        self.client.force_authenticate(user=self.owner)
        payload = {"description": "Owner comment updated."}

        response = self.client.patch(self.owner_comment_url, data=payload)
        self.assertEqual(response.status_code, 200)

        self.owner_comment.refresh_from_db()
        self.assertEqual(self.owner_comment.description, "Owner comment updated.")
        self.assertTrue(self.owner_comment.is_edited)

    def test_assignee_can_edit_own_comment(self):
        """Test that an active assignee can edit their own comment."""
        self.client.force_authenticate(user=self.assignee)
        payload = {"description": "Assignee comment updated."}

        response = self.client.patch(self.assignee_comment_url, data=payload)
        self.assertEqual(response.status_code, 200)

    def test_admin_can_delete_others_comment(self):
        """Test that an admin can delete a regular member's comment."""
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(self.assignee_comment_url)
        self.assertEqual(response.status_code, 204)

        self.assignee_comment.refresh_from_db()
        self.assertTrue(self.assignee_comment.is_deleted)

    def test_post_removal_comment_retention_and_lockout(self):
        """Test that removing an assignee retains their comments but locks them out of editing/deleting them."""
        # 1. Admin soft-deletes the assignee from the issue
        self.assignee_record.is_deleted = True
        self.assignee_record.save()

        # 2. Verify Data Retention: The comment itself was NOT soft-deleted
        self.assignee_comment.refresh_from_db()
        self.assertFalse(self.assignee_comment.is_deleted)

        # 3. Authenticate as the now-removed assignee
        self.client.force_authenticate(user=self.assignee)

        # 4. Attempt to edit the comment (Should fail)
        payload = {"description": "Trying to edit after being removed."}
        response_patch = self.client.patch(self.assignee_comment_url, data=payload)
        self.assertEqual(response_patch.status_code, 403)

        # 5. Attempt to delete the comment (Should fail)
        response_delete = self.client.delete(self.assignee_comment_url)
        self.assertEqual(response_delete.status_code, 403)
