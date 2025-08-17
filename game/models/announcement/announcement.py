from django.db import models
from django.utils import timezone


class Announcement(models.Model):
    title = models.CharField(max_length=100, default='系统公告')
    content = models.TextField(max_length=500)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title