from django.db import models

from game.models.player.player import Player


class FlorrProfile(models.Model):
    """Per-player progress of the florr-style mode."""
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='florr_profile')
    # comma separated petal items for the 5 slots, "" = empty slot, e.g. "basic:0,basic:2,,rose:1,basic:0"
    # (an item without ":rarity" is read as rarity 0)
    loadout = models.CharField(max_length=255, blank=True, default="")
    kills_total = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.player} ({self.kills_total} kills)"


class FlorrPetal(models.Model):
    """How many petals of one kind and rarity tier a player owns (equipped ones included)."""
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='florr_petals')
    kind = models.CharField(max_length=32)
    rarity = models.PositiveSmallIntegerField(default=0)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('player', 'kind', 'rarity')

    def __str__(self):
        return f"{self.player}: {self.kind}:{self.rarity} x{self.count}"
