from django.http import JsonResponse
from django.core.paginator import Paginator
from game.models.player.player import Player

def get_ranklist(request):
    try:
        page = request.GET.get('page', 1)
        page_size = 20

        players = Player.objects.all().order_by('-score')

        paginator = Paginator(players, page_size)

        try:
            current_page = paginator.page(page)
        except:
            current_page = paginator.page(1)

        ranklist = []
        base_rank = (current_page.number - 1) * page_size

        for index, player in enumerate(current_page.object_list):
            ranklist.append({
                'rank': base_rank + index+ 1,
                'username': player.user.username,
                'photo': player.photo,
                'score': player.score,
            })

        return JsonResponse({
            'result': 'success',
            'ranklist': ranklist,
            'total_players': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': current_page.number,
            'has_next': current_page.has_next(),
            'has_previous': current_page.has_previous(),
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e),
        })
