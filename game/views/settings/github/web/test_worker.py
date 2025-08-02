# views/settings/github/web/test_worker.py
from django.http import HttpResponse
from django.conf import settings
import requests
import json

WORKER_URL = "https://github-oauth-proxy.eg372933.workers.dev"


def test_worker(request):
    """测试 Cloudflare Worker"""
    results = []

    # 1. 测试 Worker 是否在线
    results.append("=== Worker 状态测试 ===")
    try:
        r = requests.get(f"{WORKER_URL}/test", timeout=10)
        data = r.json()
        results.append(f"Worker 状态: ✓ 在线")
        results.append(f"响应: {json.dumps(data, indent=2)}")
    except Exception as e:
        results.append(f"Worker 状态: ✗ {e}")

    # 2. 测试 GitHub API 中转
    results.append("\n=== GitHub API 测试 ===")
    try:
        # 测试一个无需认证的端点
        r = requests.post(
            f"{WORKER_URL}/github/access_token",
            json={
                'client_id': 'test',
                'client_secret': 'test',
                'code': 'test'
            },
            timeout=10
        )
        results.append(f"Access Token 端点: ✓ {r.status_code}")
        results.append(f"响应: {r.text[:200]}...")
    except Exception as e:
        results.append(f"Access Token 端点: ✗ {e}")

    return HttpResponse("<pre>" + "\n".join(results) + "</pre>")