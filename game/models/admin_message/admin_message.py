from django.db import models
from django.contrib.auth.models import User
from game.models.player.player import Player


class AdminMessage(models.Model):
    sender = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='sent_admin_messages')
    message = models.TextField(max_length=1000)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    reply = models.TextField(max_length=1000, blank=True, null=True)
    reply_timestamp = models.DateTimeField(blank=True, null=True)
    reply_read = models.BooleanField(default=False)  # 新增：用户是否已读回复

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.user.username} - {self.timestamp}"