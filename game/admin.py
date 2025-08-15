from django.contrib import admin
from game.models.player.player import Player
from game.models.admin_message.admin_message import AdminMessage

# Register your models here.

admin.site.register(Player)

@admin.register(AdminMessage)
class AdminMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'message', 'timestamp', 'is_read', 'reply']
    list_filter = ['is_read', 'timestamp']
    search_fields = ['sender__user__username', 'message']
    readonly_fields = ['timestamp', 'reply_timestamp']