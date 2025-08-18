from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from game.models.announcement.announcement import Announcement
from django.utils.timezone import localtime
import json


def get_announcements(request):
    """获取所有活动公告（所有用户可访问）"""
    try:
        # 获取最新的5条活跃公告
        announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:5]

        data = []
        for ann in announcements:
            data.append({
                'id': ann.id,
                'title': ann.title,
                'content': ann.content,
                'created_at': localtime(ann.created_at).strftime('%Y-%m-%d %H:%M'),
                'updated_at': localtime(ann.updated_at).strftime('%m-%d %H:%M')
            })

        # 如果是管理员，返回额外的编辑权限标记
        is_admin = request.user.is_authenticated and request.user.username == 'admin'

        return JsonResponse({
            'result': 'success',
            'announcements': data,
            'is_admin': is_admin
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })


@login_required
@require_POST
def create_announcement(request):
    """创建新公告（仅管理员）"""
    try:
        # 权限检查
        if request.user.username != 'admin':
            return JsonResponse({
                'result': 'error',
                'message': '权限不足'
            })

        data = json.loads(request.body)

        # 创建新公告
        announcement = Announcement.objects.create(
            title=data.get('title', '系统公告')[:100],
            content=data.get('content', '')[:500],
            is_active=data.get('is_active', True)
        )

        return JsonResponse({
            'result': 'success',
            'message': '公告创建成功',
            'announcement_id': announcement.id
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'result': 'error',
            'message': '无效的数据格式'
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })


@login_required
@require_POST
def update_announcement(request):
    """更新公告（仅管理员）"""
    try:
        # 权限检查
        if request.user.username != 'admin':
            return JsonResponse({
                'result': 'error',
                'message': '权限不足'
            })

        data = json.loads(request.body)
        announcement_id = data.get('id')

        if not announcement_id:
            return JsonResponse({
                'result': 'error',
                'message': '缺少公告ID'
            })

        # 获取并更新公告
        try:
            announcement = Announcement.objects.get(id=announcement_id)
            announcement.title = data.get('title', announcement.title)[:100]
            announcement.content = data.get('content', announcement.content)[:500]
            announcement.is_active = data.get('is_active', announcement.is_active)
            announcement.save()

            return JsonResponse({
                'result': 'success',
                'message': '公告更新成功'
            })
        except Announcement.DoesNotExist:
            return JsonResponse({
                'result': 'error',
                'message': '公告不存在'
            })

    except json.JSONDecodeError:
        return JsonResponse({
            'result': 'error',
            'message': '无效的数据格式'
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })


@login_required
@require_POST
def delete_announcement(request):
    """删除公告（仅管理员）"""
    try:
        # 权限检查
        if request.user.username != 'admin':
            return JsonResponse({
                'result': 'error',
                'message': '权限不足'
            })

        data = json.loads(request.body)
        announcement_id = data.get('id')

        if not announcement_id:
            return JsonResponse({
                'result': 'error',
                'message': '缺少公告ID'
            })

        # 删除公告
        try:
            announcement = Announcement.objects.get(id=announcement_id)
            announcement.delete()

            return JsonResponse({
                'result': 'success',
                'message': '公告删除成功'
            })
        except Announcement.DoesNotExist:
            return JsonResponse({
                'result': 'error',
                'message': '公告不存在'
            })

    except json.JSONDecodeError:
        return JsonResponse({
            'result': 'error',
            'message': '无效的数据格式'
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })
