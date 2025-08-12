from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings
from game.models.player.player import Player
from PIL import Image
import os
import uuid


@require_POST
@login_required
def upload_avatar(request):
    """上传用户头像"""
    try:
        # 获取上传的文件
        avatar_file = request.FILES.get('avatar')

        if not avatar_file:
            return JsonResponse({
                'result': 'error',
                'message': '请选择要上传的图片'
            })

        # 检查文件大小
        if avatar_file.size > settings.AVATAR_MAX_SIZE:
            return JsonResponse({
                'result': 'error',
                'message': f'图片大小不能超过{settings.AVATAR_MAX_SIZE // (1024 * 1024)}MB'
            })

        # 检查文件格式
        file_ext = avatar_file.name.split('.')[-1].lower()
        if file_ext not in settings.AVATAR_ALLOWED_EXTENSIONS:
            return JsonResponse({
                'result': 'error',
                'message': f'只支持以下格式：{", ".join(settings.AVATAR_ALLOWED_EXTENSIONS)}'
            })

        # 生成唯一文件名
        filename = f'{request.user.id}_{uuid.uuid4().hex[:8]}.{file_ext}'
        filepath = os.path.join(settings.MEDIA_ROOT, settings.AVATAR_UPLOAD_PATH, filename)

        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # 处理图片
        try:
            img = Image.open(avatar_file)

            # 转换为RGB（处理PNG透明通道等问题）
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img

            # 生成正方形缩略图（保持比例，裁剪中心）
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)

            # 如果不是正方形，裁剪为正方形
            if img.width != img.height:
                min_side = min(img.width, img.height)
                left = (img.width - min_side) // 2
                top = (img.height - min_side) // 2
                right = left + min_side
                bottom = top + min_side
                img = img.crop((left, top, right, bottom))
                img = img.resize((300, 300), Image.Resampling.LANCZOS)

            # 保存图片
            img.save(filepath, 'JPEG', quality=85, optimize=True)

        except Exception as e:
            return JsonResponse({
                'result': 'error',
                'message': f'图片处理失败：{str(e)}'
            })

        # 删除旧头像（如果是本地上传的）
        player = Player.objects.get(user=request.user)
        old_photo = player.photo
        if old_photo and '/media/avatars/' in old_photo:
            old_filename = old_photo.split('/')[-1]
            old_filepath = os.path.join(settings.MEDIA_ROOT, settings.AVATAR_UPLOAD_PATH, old_filename)
            if os.path.exists(old_filepath):
                try:
                    os.remove(old_filepath)
                except:
                    pass  # 删除失败也不影响

        # 更新数据库
        new_photo_url = f'{settings.MEDIA_URL}{settings.AVATAR_UPLOAD_PATH}{filename}'
        # 构建完整URL
        new_photo_url = f'https://app7549.acapp.acwing.com.cn{new_photo_url}'
        player.photo = new_photo_url
        player.save()

        return JsonResponse({
            'result': 'success',
            'message': '头像上传成功',
            'photo': new_photo_url
        })

    except Player.DoesNotExist:
        return JsonResponse({
            'result': 'error',
            'message': '用户信息不存在'
        })
    except Exception as e:
        return JsonResponse({
            'result': 'error',
            'message': str(e)
        })