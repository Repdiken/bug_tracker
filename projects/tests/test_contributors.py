from rest_framework.test import APIClient
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from projects.models import Project, Contributor

User = get_user_model()

class BaseContributorTestCase(TestCase):
    """Base class to set up common data for all contributor tests."""
    def setUp(self):
        self.client = APIClient()

        self.owner = User.objects.create_user(
            username="owner_user", password="password123"
        )
        self.member = User.objects.create_user(
            username="member_user", password="password123"
        )
        
        self.project = Project.objects.create(
            name="Merged Test Project",
            description="Testing contributor endpoints",
            owner=self.owner,
        )

        Contributor.objects.create(project=self.project, user=self.owner, role="admin")
        self.target_contributor = Contributor.objects.create(
            project=self.project, user=self.member, role="member"
        )

        self.list_url = reverse("project-contributors", args=[self.project.id])
        self.detail_url = reverse(
            "project-contributor-detail",
            args=[self.project.id, self.target_contributor.id],
        )

        # Default Authentication
        self.client.force_authenticate(user=self.owner)


class TestContributorListCreateViews(BaseContributorTestCase):
    """Tests focused on the collection endpoints (GET list, POST create)."""
    
    def setUp(self):
        super().setUp()
        # Specific to this class
        self.user_b = User.objects.create_user(
            username="user_to_be_added", password="password123123"
        )

    def test_contributor_list_GET(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_contributor_add_POST(self):
        payload = {"user": self.user_b.id, "role": "member"}
        response = self.client.post(self.list_url, data=payload)
        self.assertEqual(response.status_code, 201)

    def test_duplicate_active_contributor_check(self):
        """Test that adding an already active user throws a validation error."""
        payload = {"user": self.member.id, "role": "member"}
        response = self.client.post(self.list_url, data=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("user", response.data)

    def test_adding_a_contributor_again_after_removing(self):
        payload = {"user": self.user_b.id, "role": "member"}
        first_add_response = self.client.post(self.list_url, data=payload)
        self.assertEqual(first_add_response.status_code, 201)

        target_contributor = Contributor.objects.get(
            project=self.project, user=self.user_b
        )
        dynamic_detail_url = reverse(
            "project-contributor-detail",
            args=[self.project.id, target_contributor.id],
        )

        delete_response = self.client.delete(dynamic_detail_url)
        self.assertEqual(delete_response.status_code, 204)

        target_contributor.refresh_from_db()
        self.assertTrue(target_contributor.is_deleted)
        self.assertIsNotNone(target_contributor.deleted_at)

        second_add_response = self.client.post(self.list_url, data=payload)
        self.assertEqual(second_add_response.status_code, 201)

    def test_soft_delete_queryset_isolation(self):
        """Test that soft-deleted contributors do not appear in the GET list."""
        self.target_contributor.is_deleted = True
        self.target_contributor.save()

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

        if "results" in response.data:
            usernames = [c["user"] for c in response.data["results"]]
        else:
            usernames = [c["user"] for c in response.data]

        self.assertNotIn(self.member.username, usernames)


class TestContributorDetailViews(BaseContributorTestCase):
    """Tests focused on individual contributor records (GET, PATCH, DELETE)."""

    def test_contributor_detail_GET(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

    def test_contributor_update_PATCH_as_owner(self):
        payload = {"role": "admin"}
        response = self.client.patch(self.detail_url, data=payload)

        self.assertEqual(response.status_code, 200)
        self.target_contributor.refresh_from_db()
        self.assertEqual(self.target_contributor.role, "admin")

    def test_contributor_update_PATCH_as_unauthorized_member(self):
        self.client.force_authenticate(user=self.member)
        payload = {"role": "admin"}
        response = self.client.patch(self.detail_url, data=payload)

        self.assertEqual(response.status_code, 403)

    def test_contributor_delete_DELETE(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)

        self.target_contributor.refresh_from_db()
        self.assertTrue(self.target_contributor.is_deleted)
        self.assertIsNotNone(self.target_contributor.deleted_at)

    def test_owner_not_contributor_can_view_project(self):
        standalone_owner = User.objects.create_user(
            username="standalone_owner", password="password123"
        )
        project = Project.objects.create(
            name="Owner Only Project",
            description="No contributor record created",
            owner=standalone_owner,
        )

        self.client.force_authenticate(user=standalone_owner)
        detail_url = reverse("project-detail", args=[project.id])

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Owner Only Project")


class TestContributorPermissions(BaseContributorTestCase):
    """Tests strictly focused on verifying complex permission boundaries."""

    def setUp(self):
        super().setUp()
        # Setup specific admin constraints for these tests
        self.admin_user = User.objects.create_user(
            username="admin_user", password="password123"
        )
        Contributor.objects.create(
            project=self.project, user=self.admin_user, role="admin"
        )
        self.user_b = User.objects.create_user(
            username="user_to_be_added", password="password123123"
        )

    def test_admin_cannot_add_admin_contributor(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {"user": self.user_b.id, "role": "admin"}

        response = self.client.post(self.list_url, data=payload)
        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_remove_owner(self):
        owner_contributor = Contributor.objects.get(
            project=self.project, user=self.owner
        )
        owner_detail_url = reverse(
            "project-contributor-detail",
            args=[self.project.id, owner_contributor.id],
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(owner_detail_url)

        self.assertEqual(response.status_code, 403)
        owner_contributor.refresh_from_db()
        self.assertFalse(owner_contributor.is_deleted)

    def test_owner_can_remove_admin(self):
        admin_contributor = Contributor.objects.get(
            project=self.project, user=self.admin_user
        )
        admin_detail_url = reverse(
            "project-contributor-detail", args=[self.project.id, admin_contributor.id]
        )

        response = self.client.delete(admin_detail_url)
        self.assertEqual(response.status_code, 204)

        admin_contributor.refresh_from_db()
        self.assertTrue(admin_contributor.is_deleted)

    def test_user_cannot_remove_themselves(self):
        self.client.force_authenticate(user=self.member)

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 403)

        self.target_contributor.refresh_from_db()
        self.assertFalse(self.target_contributor.is_deleted)

    def test_admin_cannot_remove_other_admins(self):
        admin2 = User.objects.create_user(username="admin2", password="password123")
        admin2_contributor = Contributor.objects.create(
            project=self.project, user=admin2, role="admin"
        )
        admin2_url = reverse(
            "project-contributor-detail", args=[self.project.id, admin2_contributor.id]
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(admin2_url)
        self.assertEqual(response.status_code, 403)