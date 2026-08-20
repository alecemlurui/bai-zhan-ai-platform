#!/usr/bin/env python3
"""
e2e_smoke.py

端到端冒烟测试：注册 → 登录 → 创建主题 → 生成标题 → 生成文章。
用于验证 DeepSeek 真实 LLM 联调是否成功。
"""

import os
import sys
import time
from uuid import uuid4

import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


def wait_for_task(token: str, task_id: int, timeout: int = 120) -> dict:
    url = f"{BASE_URL}/api/v1/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(timeout // 2):
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data["status"] in ("success", "failed"):
            return data
        time.sleep(2)
    raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")


def main() -> int:
    username = f"smoke_{uuid4().hex[:8]}"
    password = "Smoke1234"

    print(f"[1/6] register user: {username}")
    r = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"username": username, "password": password, "email": f"{username}@test.com"},
        timeout=30,
    )
    r.raise_for_status()
    print("  -> registered")

    print("[2/6] login")
    r = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    r.raise_for_status()
    token = r.json()["access_token"]
    print("  -> got token")

    print("[3/6] create topic")
    r = requests.post(
        f"{BASE_URL}/api/v1/topics",
        json={"title": "DeepSeek 真实 LLM 联调测试", "params": {}},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    r.raise_for_status()
    topic_id = r.json()["id"]
    print(f"  -> topic_id={topic_id}")

    print("[4/6] generate titles")
    r = requests.post(
        f"{BASE_URL}/api/v1/topics/{topic_id}/generate-titles",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    r.raise_for_status()
    task = r.json()
    print(f"  -> title task_id={task['id']}, status={task['status']}")

    task = wait_for_task(token, task["id"])
    print(f"  -> title task final: {task['status']}")
    if task["status"] != "success":
        print("TASK FAILED:", task)
        return 1
    titles = requests.get(
        f"{BASE_URL}/api/v1/topics/{topic_id}/titles",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    ).json()
    print(f"  -> generated {len(titles)} titles")
    for t in titles[:3]:
        print(f"     - {t['text'][:80]}...")
    if not titles:
        print("ERROR: no titles returned")
        return 1

    title_id = titles[0]["id"]
    print(f"[5/6] generate article from title_id={title_id}")
    r = requests.post(
        f"{BASE_URL}/api/v1/articles/generate",
        json={"title_id": title_id, "use_rag": False},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    r.raise_for_status()
    task = r.json()
    print(f"  -> article task_id={task['id']}, status={task['status']}")

    task = wait_for_task(token, task["id"])
    print(f"  -> article task final: {task['status']}")
    print("  -> task.result:", task.get("result"))
    if task["status"] != "success":
        print("TASK FAILED:", task)
        return 1

    articles = requests.get(
        f"{BASE_URL}/api/v1/articles/title/{title_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    ).json()
    if not articles:
        print("ERROR: no article returned")
        return 1
    article = articles[0]
    content = article["content"]
    print(f"[6/6] article length={len(content)}")
    print("=" * 60)
    print(content[:500])
    print("=" * 60)

    # 验证不是 mock 内容
    if "模拟 LLM" in content or "mock" in content.lower():
        print("FAIL: content still looks like mock output")
        return 1

    result = task.get("result") or {}
    print(f"model={result.get('model')}  latency_ms={result.get('latency_ms')}  cost_usd={result.get('cost_usd')}")
    if not result.get("model"):
        print("WARN: task.result.model is missing")
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
