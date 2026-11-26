from django.conf import settings
from django.db import models


class TeacherProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject_specialization = models.CharField(max_length=128, blank=True)
    qualification = models.CharField(max_length=128, blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Teacher Profile'
        verbose_name_plural = 'Teacher Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Teacher"
