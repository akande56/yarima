
from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.db.models import EmailField, TextChoices
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractUser):
    """
    Default custom user model for yarima_mining.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]

    class Roles(TextChoices):
        # there is a field is_admin by default when reginsting admin user
        OFFICE_4 = 'office_4', _('Office 4')
        OFFICE_3 = 'office_3', _('Office 3')
        OFFICE_2 = 'office_2', _('Office 2')
        OFFICE_1 = 'office_1', _('Office 1')
        UNASSIGNED = 'unassigned', _('Unassigned')  # default for security

    role = CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.UNASSIGNED,
        help_text=_("User role, must be assigned by Super Admin or Office 3.")
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})
    
    def has_role(self, role_key):
        return self.role == role_key
    
    def is_office_3(self) -> bool:
        return self.role == self.Roles.OFFICE_3

    def is_office_2(self) -> bool:
        return self.role == self.Roles.OFFICE_2

    def is_office_1(self) -> bool:
        return self.role == self.Roles.OFFICE_1
    
    def __str__(self):
        return self.name