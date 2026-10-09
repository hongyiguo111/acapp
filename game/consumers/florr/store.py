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
    return text.split(",") if text else []


def load(username):
    """Returns kwargs for World.add_player. Creates the starter kit the first time."""
    player = _player_for(username)
    with transaction.atomic():
        profile, created = FlorrProfile.objects.get_or_create(
            player=player, defaults={"loadout": ",".join(w.STARTER_LOADOUT)})
        rows = FlorrPetal.objects.filter(player=player).values_list("kind", "rarity", "count")
        inventory = {w.make_item(kind, rarity): count for kind, rarity, count in rows}
        if created and not inventory:
            inventory = dict(w.STARTER_INVENTORY)
            FlorrPetal.objects.bulk_create(
                [FlorrPetal(player=player, kind=kind, rarity=rarity, count=count)
                 for (kind, rarity), count in ((w.parse_item(item), n) for item, n in inventory.items())])
    return {"inventory": inventory, "loadout": parse_loadout(profile.loadout), "kills_total": profile.kills_total}


def save(username, inventory, loadout, kills_total):
    player = _player_for(username)
    with transaction.atomic():
        FlorrProfile.objects.update_or_create(
            player=player, defaults={"loadout": ",".join(loadout), "kills_total": kills_total})
        existing = {(row.kind, row.rarity): row for row in FlorrPetal.objects.filter(player=player)}
        wanted = {}
        for item, count in inventory.items():
            parsed = w.parse_item(item)
            if parsed is not None and count > 0:
                wanted[parsed] = count
        for key, count in wanted.items():
            row = existing.get(key)
            if row is None:
                FlorrPetal.objects.create(player=player, kind=key[0], rarity=key[1], count=count)
            elif row.count != count:
                row.count = count
                row.save(update_fields=["count"])
        # items that were used up (crafting) must disappear, otherwise they come back on the next login
        for key, row in existing.items():
            if key not in wanted:
                row.delete()
