#!/usr/bin/env bash
# scripts/deploy_k8s.sh
# 部署到 Kubernetes（需先构建并推送镜像，配置好 kubectl 上下文）。
set -euo pipefail

NAMESPACE=${NAMESPACE:-bai-zhan}
IMAGE_TAG=${IMAGE_TAG:-latest}

kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml
kubectl apply -f infra/k8s/secret.yaml

# 更新镜像版本
kubectl set image deployment/bai-zhan-web web="bai-zhan-ai-platform:${IMAGE_TAG}" -n "${NAMESPACE}"
kubectl set image deployment/bai-zhan-worker worker="bai-zhan-ai-platform:${IMAGE_TAG}" -n "${NAMESPACE}"

kubectl apply -f infra/k8s/service.yaml
kubectl apply -f infra/k8s/ingress.yaml

kubectl rollout status deployment/bai-zhan-web -n "${NAMESPACE}"
kubectl rollout status deployment/bai-zhan-worker -n "${NAMESPACE}"

echo "Deployment complete. Ingress host: api.bai-zhan.example.com"
