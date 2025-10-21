from django.http import JsonResponse
from django.core.paginator import Paginator
from game.models.player.player import Player


def get_ranklist(request):
    try:
        page = request.GET.get('page', 1)
        page_size = 20

        players = Player.objects.all().order_by('-score', 'id')  # 添加id作为次要排序，保证稳定排序

        paginator = Paginator(players, page_size)

        try:
            current_page = paginator.page(page)
        except:
            current_page = paginator.page(1)

        ranklist = []
        base_rank = (current_page.number - 1) * page_size

        for index, player in enumerate(current_page.object_list):
            ranklist.append({
                'rank': base_rank + index + 1,
                'username': player.user.username,
                'photo': player.photo,
                'score': player.score,
            })

        # 获取当前登录用户的排名信息（使用连续排名逻辑）
        current_user_info = None
        if request.user.is_authenticated:
            try:
                current_player = Player.objects.get(user=request.user)

                # 计算连续排名：分数比我高的人数 + 分数和我相同但ID比我小的人数 + 1
                rank = Player.objects.filter(
                    score__gt=current_player.score
                ).count() + Player.objects.filter(
                    score=current_player.score,
                    id__lt=current_player.id
                ).count() + 1

                current_user_info = {
                    'rank': rank,
                    'username': current_player.user.username,
                    'photo': current_player.photo,
                    'score': current_player.score,
                }
            except Player.DoesNotExist:
                pass

        return JsonResponse({
            'result': 'success',
            'ranklist': ranklist,
            'total_players': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': current_page.number,
            'has_next': current_page.has_next(),
            'has_previous': current_page.has_previous(),
            'current_user': current_user_info,
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e),
        })