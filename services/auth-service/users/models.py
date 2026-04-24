"""Custom user model for auth-service."""

from __future__ import annotations

import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import Q


class UserManager(BaseUserManager["User"]):
    """Manager using email as the natural identifier."""

    def create_user(
        self,
        email: str,
        password: str | None = None,
        *,
        role: str,
        first_name: str,
        last_name: str,
        **extra_fields: object,
    ) -> User:
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str | None = None,
        *,
        first_name: str,
        last_name: str,
        **extra_fields: object,
    ) -> User:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        role = extra_fields.pop("role", User.Role.DIRECTOR)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email,
            password,
            role=role,
            first_name=first_name,
            last_name=last_name,
            **extra_fields,
        )


class User(AbstractBaseUser, PermissionsMixin):
    """Service-local user record; company_id is a logical reference (UUID only)."""

    class Role(models.TextChoices):
        DIRECTOR = "Director", "Director"
        STAFF = "Staff", "Staff"
        CLIENT = "Client", "Client"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("email address", max_length=254, unique=True, db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=16, choices=Role.choices, db_index=True)
    company_id = models.UUIDField(null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = ["first_name", "last_name"]

    class Meta:
        ordering = ("email",)
        indexes = [
            models.Index(fields=["role", "is_active"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(~Q(role="Client")) | Q(company_id__isnull=False),
                name="users_user_client_requires_company_id",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.email = type(self).objects.normalize_email(self.email)

    def __str__(self) -> str:
        return self.email
