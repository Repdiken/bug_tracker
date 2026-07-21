from django.contrib import admin
from .models import Project, Contributor

# Register your models here.


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "is_active")
    search_fields = ["name", "owner__username"]
    search_help_text = "Search by the name of the project or the project's owner"


admin.site.register(Project, ProjectAdmin)


class ContributorAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "role")


admin.site.register(Contributor, ContributorAdmin)
