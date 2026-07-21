from django.contrib import admin
from .models import Issue, Comment, IssueAssignee


class IssueAdmin(admin.ModelAdmin):
    list_display = ["project", "name", "creator", "is_deleted"]
    search_fields = ["project"]
    search_help_text = (
        "Search by the project to see all the issues from a particular project"
    )


admin.site.register(Issue, IssueAdmin)


class CommentAdmin(admin.ModelAdmin):
    list_display = ["project", "issue", "author", "is_deleted"]
    search_fields = ["project", "issue"]
    search_help_text = (
        "Search by the project to see all the comments from a particular project"
    )

    def project(self, obj):
        return obj.issue.project

    project.admin_order_field = "issue__project"
    project.short_description = "Project"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("issue", "issue__project")


class IssueAssigneeAdmin(admin.ModelAdmin):
    list_display = ["user", "issue", "is_deleted"]


admin.site.register(IssueAssignee, IssueAssigneeAdmin)


admin.site.register(Comment, CommentAdmin)
