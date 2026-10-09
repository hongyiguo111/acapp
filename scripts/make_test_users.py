"""Create local-only test accounts (florr_a / florr_b, password: test1234) in the LOCAL db.sqlite3.

    .venv\\Scripts\\python.exe manage.py shell -c "exec(open('scripts/make_test_users.py', encoding='utf-8').read())"
Never run this against the production database.
"""
from django.conf import settings
from django.contrib.auth.models import User
from game.models.player.player import Player

assert not str(settings.BASE_DIR).startswith("/home/acs"), "refusing to run on the server"
for name in ("florr_a", "florr_b"):
    user, created = User.objects.get_or_create(username=name)
    user.set_password("test1234")
    user.save()
    Player.objects.get_or_create(user=user, defaults={"photo": ""})
    print(name, "created" if created else "updated")
