from django.test import SimpleTestCase
from django.urls import reverse, resolve

from projects.views import (
    ProjectListCreateView,
    ProjectDetailUpdateDeleteView,
    ProjectOwnershipTransferView,
    ContributorListCreateView,
    ContributorDetailUpdateDeleteViews,
)


class TestProjectUrls(SimpleTestCase):

    def test_list_url_is_resolved(self):
        url = reverse("project-list")

        self.assertEqual(
            resolve(url).func.view_class,
            ProjectListCreateView,
        )

    def test_detail_url_is_resolved(self):
        url = reverse(
            "project-detail",
            kwargs={"project_id": 1},
        )

        self.assertEqual(
            resolve(url).func.view_class,
            ProjectDetailUpdateDeleteView,
        )

    def test_contributor_list_url_is_resolved(self):
        url = reverse(
            "project-contributors",
            kwargs={"project_id": 1},
        )

        self.assertEqual(
            resolve(url).func.view_class,
            ContributorListCreateView,
        )

    def test_contributor_detail_url_is_resolved(self):
        url = reverse(
            "project-contributor-detail",
            kwargs={
                "project_id": 1,
                "contributor_id": 1,
            },
        )

        self.assertEqual(
            resolve(url).func.view_class,
            ContributorDetailUpdateDeleteViews,
        )

    def test_project_ownership_url_is_resolved(self):
        url = reverse("project-transfer-ownership", kwargs={"project_id": 1})

        self.assertEqual(resolve(url).func.view_class, ProjectOwnershipTransferView)
