#!/usr/bin/env bash
# scripts/e2e_test.sh
# 端到端验收脚本：注册 -> 登录 -> 创建主题 -> 生成标题 -> 生成文章（RAG）-> 生成封面 -> 发布 -> 查询发布历史。
# 用法：BASE_URL=http://localhost:8000 ./scripts/e2e_test.sh
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}
USERNAME="e2e_user_$(date +%s)"
PASSWORD="testpass123"

echo "==> 1. Register user"
curl -s -X POST "${BASE_URL}/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}" | jq .

echo "==> 2. Login"
TOKEN=$(curl -s -X POST "${BASE_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}" | jq -r '.access_token')

AUTH="Authorization: Bearer ${TOKEN}"

echo "==> 3. Create topic"
TOPIC_ID=$(curl -s -X POST "${BASE_URL}/api/v1/topics" \
  -H "Content-Type: application/json" \
  -H "${AUTH}" \
  -d '{"title":"高考数学复习","params":{"style":"xiaohongshu"}}' | jq -r '.id')
echo "Topic ID: ${TOPIC_ID}"

echo "==> 4. Generate titles"
TASK_ID=$(curl -s -X POST "${BASE_URL}/api/v1/topics/${TOPIC_ID}/generate-titles" \
  -H "${AUTH}" | jq -r '.id')
echo "Title task ID: ${TASK_ID}"

sleep 1

echo "==> 5. Query task status"
curl -s "${BASE_URL}/api/v1/tasks/${TASK_ID}" -H "${AUTH}" | jq .

echo "==> 6. List titles and pick first"
TITLE_ID=$(curl -s "${BASE_URL}/api/v1/titles/topic/${TOPIC_ID}" -H "${AUTH}" | jq -r '.[0].id')
echo "Title ID: ${TITLE_ID}"

echo "==> 7. Generate article with RAG"
ARTICLE_TASK_ID=$(curl -s -X POST "${BASE_URL}/api/v1/articles/generate" \
  -H "Content-Type: application/json" \
  -H "${AUTH}" \
  -d "{\"title_id\":${TITLE_ID},\"use_rag\":true,\"rag_query\":\"高考数学复习\"}" | jq -r '.id')
echo "Article task ID: ${ARTICLE_TASK_ID}"

sleep 2

echo "==> 8. Query article task"
curl -s "${BASE_URL}/api/v1/tasks/${ARTICLE_TASK_ID}" -H "${AUTH}" | jq .

echo "==> 9. List articles and pick first"
ARTICLE_ID=$(curl -s "${BASE_URL}/api/v1/articles/title/${TITLE_ID}" -H "${AUTH}" | jq -r '.[0].id')
echo "Article ID: ${ARTICLE_ID}"

echo "==> 10. Generate cover"
curl -s -X POST "${BASE_URL}/api/v1/articles/generate-cover" \
  -H "Content-Type: application/json" \
  -H "${AUTH}" \
  -d "{\"article_id\":${ARTICLE_ID},\"prompt\":\"高考数学复习封面\",\"width\":512,\"height\":512}" | jq .

echo "==> 11. Bind platform account"
ACCOUNT_ID=$(curl -s -X POST "${BASE_URL}/api/v1/accounts" \
  -H "Content-Type: application/json" \
  -H "${AUTH}" \
  -d '{"platform":"xiaohongshu","account_name":"官方号","credentials":{}}' | jq -r '.id')
echo "Account ID: ${ACCOUNT_ID}"

echo "==> 12. Publish"
PUBLISH_TASK_ID=$(curl -s -X POST "${BASE_URL}/api/v1/publish" \
  -H "Content-Type: application/json" \
  -H "${AUTH}" \
  -d "{\"article_id\":${ARTICLE_ID},\"platform\":\"xiaohongshu\",\"account_id\":${ACCOUNT_ID}}" | jq -r '.id')
echo "Publish task ID: ${PUBLISH_TASK_ID}"

sleep 1

echo "==> 13. Query publish task"
curl -s "${BASE_URL}/api/v1/tasks/${PUBLISH_TASK_ID}" -H "${AUTH}" | jq .

echo "==> 14. Query publish records"
curl -s "${BASE_URL}/api/v1/publish/article/${ARTICLE_ID}" -H "${AUTH}" | jq .

echo "==> E2E smoke test complete"
