from django.db import models
from django.contrib.auth.models import User

class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.URLField(max_length=256, blank=True)
    openid = models.CharField(default="", max_length=50, blank=True, null=True)

    github_id = models.CharField(default="", max_length=256, blank=True, null=True)
    github_username = models.CharField(default="", max_length=256, blank=True, null=True)

    # Gitee 字段（新增）
    gitee_id = models.CharField(default="", max_length=256, blank=True, null=True)
    gitee_username = models.CharField(default="", max_length=256, blank=True, null=True)
    
    def __str__(self):
        return str(self.user)