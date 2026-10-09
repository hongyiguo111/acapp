from django.http import JsonResponse

from game.models.florr.florr import FlorrProfile

TOP_N = 20


def get_florr_ranklist(request):
    """Lifetime kills in the florr-style mode. Same shape as the duel ranklist: a top list and the caller's own rank."""
    profiles = FlorrProfile.objects.filter(kills_total__gt=0).select_related('player__user')
    top = profiles.order_by('-kills_total', 'id')[:TOP_N]
    ranklist = [{
        'rank': index + 1,
        'username': profile.player.user.username,
        'photo': profile.player.photo,
        'kills': profile.kills_total,
    } for index, profile in enumerate(top)]

    current_user = None
    if request.user.is_authenticated:
        mine = profiles.filter(player__user=request.user).first()
        if mine is not None:
            rank = profiles.filter(kills_total__gt=mine.kills_total).count() \
                + profiles.filter(kills_total=mine.kills_total, id__lt=mine.id).count() + 1
            current_user = {
                'rank': rank,
                'username': request.user.username,
                'photo': mine.player.photo,
                'kills': mine.kills_total,
            }
    return JsonResponse({'result': 'success', 'ranklist': ranklist, 'current_user': current_user})
