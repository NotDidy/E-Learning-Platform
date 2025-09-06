from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        INSTRUCTOR = "INSTRUCTOR", "Instructor"
        STUDENT = "STUDENT", "Student"

    # Override to make email unique (AbstractUser’s default isn't unique)
    email = models.EmailField(unique=True)

    TITLE_CHOICES = [("MR", "Mr"), ("MRS", "Mrs"), ("MS", "Ms"), ("DR", "Dr")]
    title = models.CharField(max_length=5, choices=TITLE_CHOICES, blank=True, null=True)

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.STUDENT)

    def save(self, *args, **kwargs):
        # Always keep username in sync with email (lowercased)
        if self.email:
            self.email = self.email.strip().lower()
            self.username = self.email
        super().save(*args, **kwargs)
