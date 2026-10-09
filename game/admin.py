from django.contrib import admin
from game.models.player.player import Player
from game.models.admin_message.admin_message import AdminMessage
from game.models.florr.florr import FlorrProfile, FlorrPetal

# Register your models here.

admin.site.register(Player)
admin.site.register(FlorrProfile)
admin.site.register(FlorrPetal)

@admin.register(AdminMessage)
class AdminMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'message', 'timestamp', 'is_read', 'reply']
    list_filter = ['is_read', 'timestamp']
    search_fields = ['sender__user__username', 'message']
    readonly_fields = ['timestamp', 'reply_timestamp']