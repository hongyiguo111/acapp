from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


@login_required
def check_username(request):
    """检查用户名是否可用"""
    username = request.GET.get('username', '').strip()

    if not username:
        return JsonResponse({
            'result': 'error',
            'available': False,
            'message': '用户名不能为空'
        })

    if len(username) < 3:
        return JsonResponse({
            'result': 'error',
            'available': False,
            'message': '用户名至少需要3个字符'
        })

    if len(username) > 20:
        return JsonResponse({
            'result': 'error',
            'available': False,
            'message': '用户名不能超过20个字符'
        })

    # 检查是否是当前用户的用户名
    if username == request.user.username:
        return JsonResponse({
            'result': 'success',
            'available': True,
            'message': '当前用户名'
        })

    # 检查用户名是否已存在
    if User.objects.filter(username=username).exists():
        return JsonResponse({
            'result': 'error',
            'available': False,
            'message': '用户名已被使用'
        })

    return JsonResponse({
        'result': 'success',
        'available': True,
        'message': '用户名可用'
    })