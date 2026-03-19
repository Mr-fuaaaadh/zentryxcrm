from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import os
import uuid

from apps.accounts.managers import UserManager


def user_profile_image_path(instance, filename):
    """
    Generates a unique path for user profile images.
    Format: profile_images/<year>/<month>/<uuid>.<ext>
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('profile_images', timezone.now().strftime('%Y/%m'), filename)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for the CRM system.
    Supports multiple roles and uses email as the primary identifier.
    """

    ROLE_CHOICES = (
        ('ADMIN', _('Admin')),
        ('HR', _('HR')),
        ('STAFF', _('Staff')),
        ('STUDENT', _('Student')),
        ('SALES', _('Sales')),
        ('TRAINER', _('Trainer')),
    )

    email = models.EmailField(
        _("Email Address"),
        unique=True,
        db_index=True,
        help_text=_("Required. Primary identifier for login.")
    )
    username = models.CharField(
        _("Username"),
        max_length=150,
        unique=True,
        help_text=_("Required. 150 characters or fewer.")
    )

    first_name = models.CharField(_("First Name"), max_length=150, blank=True)
    last_name = models.CharField(_("Last Name"), max_length=150, blank=True)

    role = models.CharField(
        _("Role"),
        max_length=20,
        choices=ROLE_CHOICES,
        default='STUDENT'
    )
    profile_image = models.ImageField(
        _("Profile Image"),
        upload_to=user_profile_image_path,
        null=True,
        blank=True,
        help_text=_("Max size: 5MB. Formats: JPG, PNG, GIF.")
    )

    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_("Designates whether this user should be treated as active.")
    )
    is_staff = models.BooleanField(
        _("Staff Status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site.")
    )
    is_superuser = models.BooleanField(
        _("Superuser Status"),
        default=False,
        help_text=_("Designates that this user has all permissions without explicitly assigning them.")
    )

    date_joined = models.DateTimeField(_("Date Joined"), default=timezone.now)
    is_email_verified = models.BooleanField(_("Email Verified"), default=False)
    
    objects = UserManager()   # 🔥 VERY IMPORTANT


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['-date_joined']
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def get_full_name(self) -> str:
        """Returns the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username

    def get_short_name(self) -> str:
        """Returns the short name for the user."""
        return self.first_name or self.username

    def __str__(self) -> str:
        return self.get_full_name()

