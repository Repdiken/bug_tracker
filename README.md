# BugTracker API

A secure RESTful Bug Tracking API built with **Django** and **Django REST Framework**.

This project was created as a learning project during my Web Security internship to gain hands-on experience with backend development, REST API design, authentication, authorization, and secure software development principles. Rather than focusing only on making a working CRUD application, the goal was to understand how secure APIs are designed, how permissions should be implemented, and how common web vulnerabilities can be prevented.

---

# Project Goals

The primary objectives of this project were:

- Learn Django and Django REST Framework
- Design a relational database from scratch
- Implement a complete RESTful API
- Learn JWT authentication
- Implement role-based authorization
- Implement object-level permissions
- Design nested REST endpoints
- Maintain database integrity
- Prevent unauthorized data access
- Learn how generic views work internally
- Apply secure API development principles

Instead of relying on Django REST Framework's abstractions immediately, many features were first implemented manually in order to understand what DRF performs internally before transitioning to generic views.

---

# Features

## Authentication

- JWT Authentication
- User Registration
- User Login
- Token Refresh
- Protected API endpoints

---

## Project Management

Users can

- Create projects
- View projects they belong to
- Update their own projects
- Soft delete projects
- Project owners can transfer their ownership to an active project contributor.
- Standard members and admins can leave a project at any time, which soft-deletes their contributor record.
- Project owners are blocked from leaving a project; they must transfer ownership or delete the project entirely
- A strict validation limit enforces that a single user cannot own more than 20 active projects.

Every project has a single owner.

---

## Contributors

Projects contain contributors.

Each contributor can have one of the following roles:

- Admin
- Member

The project owner is stored separately as the project's `owner` field and therefore always has full control regardless of contributor role.

Project owners can

- Add contributors
- Remove contributors
- Promote contributors to administrators

Administrators have elevated privileges but cannot perform actions reserved for the project owner.

---

## Issues

Each project can contain multiple issues.

Issues include

- Name
- Description
- Priority
- Deadline
- Creator

Issues can be

- Created
- Retrieved
- Updated
- Soft deleted

---

## Issue Assignees

Each issue can have multiple assigned users.

Validation ensures that

- only project contributors can be assigned to issues.

Attempting to assign a user who does not belong to the project results in a validation error.

---

## Comments

Each issue supports comments.

Comments include

- Author
- Description
- Creation date
- Edited status

Comment ownership is enforced through custom object-level permissions.

---

# Security Features

This project focuses heavily on secure API development.

The following security mechanisms were implemented.

## JWT Authentication

Only authenticated users can access protected endpoints.

---

## Object-Level Authorization

Custom permission classes were created to ensure users only access resources they are authorized to use.

Permissions include:

- IsProjectOwner
- IsProjectAdmin
- IsProjectContributor
- IsIssueAssignee
- IsCommentOwner

---

## Role-Based Access Control

Different operations require different permissions.

For example

| Operation | Required Role |
|------------|---------------|
| View project | Contributor |
| Create contributor | Owner/Admin |
| Update contributor | Owner |
| Delete contributor | Owner/Admin (Members only) |
| Create issue | Admin/Owner |
| Assign users | Admin/Owner |
| Comment on issue | Assigned user |
| Edit own comment | Comment owner |

---

## Queryset Filtering

Instead of exposing objects and denying access afterwards, querysets are filtered according to the authenticated user.

This prevents users from discovering resources belonging to other projects.

Example:

A user requesting

```
/projects/5/
```

will receive a 404 response if they are not a contributor of Project 5.

---

## Serializer Validation

Business rules are enforced using serializer validation.

Examples include

- only project contributors may become issue assignees
- duplicate relationships are prevented
- invalid foreign key relationships are rejected

---

## Soft Delete

Most entities are soft deleted.

Instead of permanently removing records,

```
is_deleted=True
deleted_at=<timestamp>
```

is stored.

Soft-deleted resources are automatically excluded from API responses.

---

# Technologies Used

- Python
- Django
- Django REST Framework
- JWT Authentication (SimpleJWT)
- SQLite
- Django ORM

---

# Database Structure

![alt text](<models_sketch.png>)
First sketch of the database structure (some models might have changed in the development stage).

## User

Represents an authenticated user.

Relationships

- Owns Projects
- Creates Issues
- Writes Comments
- Can become Contributor
- Can become Issue Assignee

---

## Project

A project represents a workspace.

Fields include

- Owner
- Name
- Description
- is_deleted
- created_at
- updated_at

Relationships

```
Project
│
├── Contributors
├── Issues
│   ├── Comments
│   └── Assignees
```

---

## Contributor

Represents membership inside a project.

Fields

- User
- Project
- Role

Role options

- Admin
- Member

---

## Issue

Represents a bug or task.

Fields include

- Creator
- Project
- Name
- Description
- Priority
- Deadline

Relationships

- belongs to one Project
- has many Comments
- has many Assignees

---

## IssueAssignee

Connects Users to Issues.

Validation ensures the assigned user belongs to the project.

---

## Comment

Represents discussion attached to an issue.

Each comment belongs to

- one Issue
- one Author

---

# API Structure

```
auth/users
│
├── GET
└── POST

auth/jwt/create
│
└── POST

projects/
│
├── GET
└── POST

projects/<project_id>/
│
├── GET
├── PATCH
└── DELETE

projects/<project_id>/transfer-ownership/
│
└── POST

projects/<project_id>/leave/
│
└── POST

projects/<project_id>/contributors/
│
├── GET
└── POST

projects/<project_id>/contributors/<contributor_id>/
│
├── GET
├── PATCH
└── DELETE

projects/<project_id>/issues/
│
├── GET
└── POST

projects/<project_id>/issues/<issue_id>/
│
├── GET
├── PATCH
└── DELETE

projects/<project_id>/issues/<issue_id>/comments/
│
├── GET
└── POST

projects/<project_id>/issues/<issue_id>/comments/<comment_id>/
│
├── GET
├── PATCH
└── DELETE

projects/<project_id>/issues/<issue_id>/assignees/
│
├── GET
└── POST

projects/<project_id>/issues/<issue_id>/assignees/<assignee_id>/
│
└── DELETE
```

---

# Authentication

The API uses JWT authentication.


1. Register in **auth/users/** by filing the cardentials
2. Receive an Access Token in **auth/jwt/create**
3. Include the Token using Header Editor Light extension, Postman or any other method of your choice in every request


```
Authorization: Bearer <access_token>
```


---

# Running the Project

## Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/BugTracker.git

cd BugTracker
```

---

## Create a virtual environment

```bash
python -m venv .venv
```

---

## Activate it

Windows

```bash
.venv\Scripts\activate
```

Linux / macOS

```bash
source .venv/bin/activate
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

## Create a `.env`

Example

```
SECRET_KEY=your_secret_key
DEBUG=True
```

---

## Apply migrations

```bash
python manage.py migrate
```

---

## Create a superuser

```bash
python manage.py createsuperuser
```

---

## Start the server

```bash
python manage.py runserver
```

---

# Important Notes

Before running the project:

- create your own `.env`
- never upload your `.env`
- generate your own `SECRET_KEY`
- create your own superuser

---

# Lessons Learned

This project evolved far beyond a simple CRUD application.

During development I learned

- proper database design
- REST API architecture
- nested routing
- generic views
- serializer validation
- custom permissions
- object-level authorization
- queryset filtering
- soft deletion
- secure authentication
- role-based access control
- preventing privilege escalation
- preventing unauthorized resource access

One of the biggest lessons learned was the importance of planning software before implementation. Many architectural decisions—including permissions, nested resources, validation rules, and data relationships—were discovered during development rather than before it began. This project highlighted the value of software design, requirement analysis, and iterative improvement while providing practical experience building secure backend systems.

---

# Future Improvements

Possible future enhancements include

- Email verification
- Password reset via email
- Two-factor authentication (2FA)
- Project invitations
- Notifications
- File attachments
- Labels
- Issue status workflow
- Project archiving
- API documentation (Swagger/OpenAPI)
- Docker support
- PostgreSQL deployment
- CI/CD pipeline

---

# License

This project was created for educational purposes and to practice secure backend development and web security using Django REST Framework.