# Functions I used for views before moving to generic views. Some of them may include bugs or problems.


# @api_view(["GET", "POST"])
# @permission_classes([IsAuthenticated])
# def project_list_create(request):
#     if request.method == "GET":
#         # Give me unique projects where the current user appears in the contributors table
#         queryset = Project.objects.filter(
#             contributors__user=request.user, is_deleted=False
#         ).distinct()
#         serilizer = ProjectListSerializer(
#             queryset,
#             many=True,
#             context={"request": request},
#         )
#         return Response(serilizer.data)
#     elif request.method == "POST":
#         serializer = ProjectCreateSerializer(
#             data=request.data, context={"request": request}
#         )
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)


# @api_view(["GET", "PATCH", "DELETE"])
# @permission_classes([IsAuthenticated])
# def project_detail_delete(request, id):
#     project = get_object_or_404(
#         Project.objects.filter(contributors__user=request.user).distinct(), pk=id
#     )

#     if request.method == "GET":
#         serilizer = ProjectDetailSerializer(project, context={"request": request})
#         return Response(serilizer.data)

#     elif request.method == "PATCH":
#         serializer = ProjectDetailSerializer(
#             project,
#             data=request.data,
#             partial=True,  # If you forget partial=True, DRF treats PATCH like PUT - Missing fields → 400 Bad Request
#         )
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)

#     elif request.method == "DELETE":

#         project = get_object_or_404(
#             Project,
#             pk=id,
#             contributors__user=request.user,
#             is_deleted=False,
#         )

#         project.is_deleted = True
#         project.deleted_at = now()
#         project.save(update_fields=["is_deleted", "deleted_at"])

#         return Response(
#             {"detail": "Project deleted successfully."},
#             status=status.HTTP_204_NO_CONTENT,
#         )


# class ProjectDetailView(APIView):

#     def get_permissions(self):
#         if self.request.method == "GET":
#             return [IsAuthenticated()]
#         return [IsAuthenticated(), IsProjectOwner()]

#     def get_object(self, id):
#         return get_object_or_404(Project, pk=id, is_deleted=False)

#     def get(self, request, id):
#         project = self.get_object(id)
#         serializer = ProjectDetailSerializer(project, context={"request": request})
#         return Response(serializer.data)

#     def patch(self, request, id):
#         project = self.get_object(id)
#         self.check_object_permissions(request, project)

#         serializer = ProjectDetailSerializer(project, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)

#     def delete(self, request, id):
#         project = self.get_object(id)
#         self.check_object_permissions(request, project)

#         project.is_deleted = True
#         project.deleted_at = now()
#         project.save(update_fields=["is_deleted", "deleted_at"])

#         return Response(status=status.HTTP_204_NO_CONTENT)


# @api_view(["GET", "POST", "PATCH", "DELETE"])
# def contributor_list_add_edit(request, id):
#     if request.method == "GET":
#         contributors = Contributor.objects.filter(
#             project_id=id
#         )  # SELECT * FROM contributor WHERE project_id = id
#         serializer = ContributorListSerializer(contributors, many=True)
#         return Response(
#             serializer.data
#         )  # Get all contributors for a project, convert them to JSON, return them to the client
#     if request.method == "POST":
#         serializer = ContributorCreateUpdateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(project_id=id)
#         return Response(serializer.data, status=201)
#     if request.method == "PATCH":
#         contributor = get_object_or_404(
#             Contributor,
#             project_id=id,
#             user_id=request.data.get("user"),
#         )

#         serializer = ContributorCreateUpdateSerializer(
#             contributor,
#             data=request.data,
#             partial=True,
#         )
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)
#     if request.method == "DELETE":
#         pass


# class ContributorView(APIView):
#     def get_permissions(self):
#         if self.request.method == "GET":
#             return [IsAuthenticated()]
#         elif self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
#             return [IsAuthenticated(), IsProjectOwner()]
#         return [IsAuthenticated()]

#     def get(self, request, project_id, contributor_id=None):

#         is_contributor = Contributor.objects.filter(
#             project_id=project_id,
#             user=request.user,
#             is_deleted=False,
#         ).exists()

#         if not is_contributor:
#             raise PermissionDenied("You are not a contributor of this project.")

#         if contributor_id is None:
#             contributors = Contributor.objects.filter(
#                 project_id=project_id,
#                 is_deleted=False,
#             )
#             serializer = ContributorListSerializer(
#                 contributors, many=True, context={"request": request}
#             )
#             return Response(serializer.data)

#         contributor = get_object_or_404(
#             Contributor, pk=contributor_id, project_id=project_id, is_deleted=False
#         )
#         serializer = ContributorListSerializer(
#             contributor, context={"request": request}
#         )
#         return Response(serializer.data)

#     def post(self, request, project_id):
#         project = get_object_or_404(Project, pk=project_id, is_deleted=False)
#         self.check_object_permissions(request, project)

#         serializer = ContributorCreateUpdateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(project_id=project_id)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)

#     def patch(self, request, project_id, contributor_id):
#         project = get_object_or_404(Project, pk=project_id, is_deleted=False)
#         self.check_object_permissions(request, project)

#         contributor = get_object_or_404(
#             Contributor,
#             pk=contributor_id,
#             project_id=project_id,
#         )
#         serializer = ContributorCreateUpdateSerializer(
#             contributor, data=request.data, partial=True
#         )
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)

#     def delete(self, request, project_id, contributor_id):
#         project = get_object_or_404(Project, pk=project_id, is_deleted=False)
#         self.check_object_permissions(request, project)

#         contributor = get_object_or_404(
#             Contributor,
#             pk=contributor_id,
#             project_id=project_id,
#         )
#         contributor.is_deleted = True
#         contributor.deleted_at = now()
#         contributor.save(update_fields=["is_deleted", "deleted_at"])

#         return Response(status=status.HTTP_204_NO_CONTENT)


# class ContributorView(APIView):
#     def get_permissions(self):
#         if self.request.method == "GET":
#             return [IsAuthenticated()]
#         elif self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
#             return [IsAuthenticated(), IsProjectOwner()]
#         return [IsAuthenticated()]

#     def get(self, request, project_id, contributor_id=None):

#         is_contributor = Contributor.objects.filter(
#             project_id=project_id,
#             user=request.user,
#             is_deleted=False,
#         ).exists()

#         if not is_contributor:
#             raise PermissionDenied("You are not a contributor of this project.")

#         if contributor_id is None:
#             contributors = Contributor.objects.filter(
#                 project_id=project_id,
#                 is_deleted=False,
#             )
#             serializer = ContributorListSerializer(
#                 contributors, many=True, context={"request": request}
#             )
#             return Response(serializer.data)

#         contributor = get_object_or_404(
#             Contributor, pk=contributor_id, project_id=project_id, is_deleted=False
#         )
#         serializer = ContributorListSerializer(
#             contributor, context={"request": request}
#         )
#         return Response(serializer.data)

#     def post(self, request, project_id):
#         project = get_object_or_404(Project, pk=project_id, is_deleted=False)
#         self.check_object_permissions(request, project)

#         serializer = ContributorCreateUpdateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(project_id=project_id)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)

#     def patch(self, request, project_id, contributor_id):
#         project = get_object_or_404(Project, pk=project_id, is_deleted=False)
#         self.check_object_permissions(request, project)

#         contributor = get_object_or_404(
#             Contributor,
#             pk=contributor_id,
#             project_id=project_id,
#         )
#         serializer = ContributorCreateUpdateSerializer(
#             contributor, data=request.data, partial=True
#         )
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)

#     def delete(self, request, project_id, contributor_id):
#         project = get_object_or_404(Project, pk=project_id, is_deleted=False)
#         self.check_object_permissions(request, project)

#         contributor = get_object_or_404(
#             Contributor,
#             pk=contributor_id,
#             project_id=project_id,
#         )
#         contributor.is_deleted = True
#         contributor.deleted_at = now()
#         contributor.save(update_fields=["is_deleted", "deleted_at"])

#         return Response(status=status.HTTP_204_NO_CONTENT)


# @api_view(["GET", "POST"])
# @permission_classes([IsProjectContributor])
# def issue_list_create(request, project_id):

#     if request.method == "GET":
#         issues = Issue.objects.filter(
#             project_id=project_id, project__contributors__user=request.user
#         )
#         serializer = IssueListSerializer(
#             issues, many=True, context={"request": request}
#         )
#         return Response(serializer.data)

#     elif request.method == "POST":
#         project = get_object_or_404(
#             Project, pk=project_id, contributors__user=request.user
#         )
#         serializer = IssueCreateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save(project=project, creator=request.user)
#         return Response(serializer.data, status=201)


# @api_view(["GET"])
# @permission_classes([IsProjectContributor])
# def issue_detail(request, project_id, issue_id):
#     issue = get_object_or_404(Issue, project_id=project_id, id=issue_id)
#     serializer = IssueDetailSerializer(issue)
#     return Response(serializer.data)
