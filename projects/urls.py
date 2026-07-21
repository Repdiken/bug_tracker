from django.urls import path
from .views import (
    ProjectListCreateView,
    ProjectDetailUpdateDeleteView,
    ContributorListCreateView,
    ContributorDetailUpdateDeleteViews,
)

urlpatterns = [
    path("projects/", ProjectListCreateView.as_view(), name="project-list"),
    path(
        "projects/<int:project_id>/",
        ProjectDetailUpdateDeleteView.as_view(),
        name="project-detail",
    ),
    path(
        "projects/<int:project_id>/contributors/",
        ContributorListCreateView.as_view(),
        name="project-contributors",
    ),
    path(
        "projects/<int:project_id>/contributors/<int:contributor_id>/",
        ContributorDetailUpdateDeleteViews.as_view(),
        name="project-contributor-detail",
    ),
]
