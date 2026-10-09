"""Database access for florr progress. Plain synchronous functions: callers wrap them with
`database_sync_to_async`. The simulation (world.py) never touches the database."""
from django.contrib.auth.models import User
from django.db import transaction

from game.models.florr.florr import FlorrPetal, FlorrProfile
from game.models.player.player import Player

from . import world as w


def _player_for(username):
    user = User.objects.get(username=username)
    player, _ = Player.objects.get_or_create(user=user)
    return player


def parse_loadout(text):
    return (text or "").split(",") if text else []


def load(username):
    """Returns kwargs for World.add_player. Creates the starter kit the first time."""
    player = _player_for(username)
    with transaction.atomic():
        profile, created = FlorrProfile.objects.get_or_create(
            player=player, defaults={"loadout": ",".join(w.STARTER_LOADOUT)})
        inventory = dict(FlorrPetal.objects.filter(player=player).values_list("kind", "count"))
        if created and not inventory:
            inventory = dict(w.STARTER_INVENTORY)
            FlorrPetal.objects.bulk_create(
                [FlorrPetal(player=player, kind=k, count=c) for k, c in inventory.items()])
    return {"inventory": inventory, "loadout": parse_loadout(profile.loadout), "kills_total": profile.kills_total}


def save(username, inventory, loadout, kills_total):
    player = _player_for(username)
    with transaction.atomic():
        FlorrProfile.objects.update_or_create(
            player=player, defaults={"loadout": ",".join(loadout), "kills_total": kills_total})
        for kind, count in inventory.items():
            FlorrPetal.objects.update_or_create(player=player, kind=kind, defaults={"count": count})
