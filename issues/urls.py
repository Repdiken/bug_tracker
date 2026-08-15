from django.urls import path
from .views import (
    IssueListCreateView,
    IssueDetailUpdateDeleteView,
    CommentListCreateView,
    CommentDetailUpdateDelete,
    IssueAssigneeListCreateView,
    IssueAssigneeDetailDeleteView,
)

urlpatterns = [
    path(
        "projects/<int:project_id>/issues/",
        IssueListCreateView.as_view(),
        name="project-issues",
    ),
    path(
        "projects/<int:project_id>/issues/<int:issue_id>",
        IssueDetailUpdateDeleteView.as_view(),
        name="issue-detail",
    ),
    path(
        "projects/<int:project_id>/issues/<int:issue_id>/comments/",
        CommentListCreateView.as_view(),
        name="issue_comments",
    ),
    path(
        "projects/<int:project_id>/issues/<int:issue_id>/comments/<int:comment_id>",
        CommentDetailUpdateDelete.as_view(),
        name="comment_detail",
    ),
    path(
        "projects/<int:project_id>/issues/<int:issue_id>/assignees/",
        IssueAssigneeListCreateView.as_view(),
        name="issue-assignees",
    ),
    path(
        "projects/<int:project_id>/issues/<int:issue_id>/assignees/<int:assignee_id>/",
        IssueAssigneeDetailDeleteView.as_view(),
        name="assignee_detail",
    ),
]
