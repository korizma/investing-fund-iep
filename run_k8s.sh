#!/usr/bin/env bash

set -e

cd "$(dirname "$0")"

minikube start

docker build -t iep-auth:v1 ./auth_service
docker build -t iep-employee:v1 ./employee_service
docker build -t iep-director:v1 ./director_service

minikube image load iep-auth:v1
minikube image load iep-employee:v1
minikube image load iep-director:v1

kubectl apply -f k8s/kubernetes.yaml
kubectl wait --for=condition=available deployment --all --timeout=180s

kubectl get pods
kubectl get services

kubectl port-forward service/auth-service-app 5000:5000 &
auth_forward_pid=$!

kubectl port-forward service/employee-service-app 5001:5001 &
employee_forward_pid=$!

kubectl port-forward service/director-service-app 5002:5002 &
director_forward_pid=$!

kubectl port-forward service/ganache 8545:8545 &
ganache_forward_pid=$!

trap 'kill "$auth_forward_pid" "$employee_forward_pid" "$director_forward_pid" "$ganache_forward_pid" 2>/dev/null || true' EXIT

echo "Services are available at:"
echo "  Auth:     http://127.0.0.1:5000"
echo "  Employee: http://127.0.0.1:5001"
echo "  Director: http://127.0.0.1:5002"
echo "  Ganache:  http://127.0.0.1:8545"
echo "Press Ctrl+C to stop."

wait
