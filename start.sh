#!/bin/bash
set -euo pipefail
trap "echo 'Encerrando...'; kill 0" EXIT

echo "Fake News Detector"
echo "=============================="

if [ ! -f .env ]; then
  echo "Arquivo .env não encontrado. Copie .env.example e configure as chaves."
  exit 1
fi

echo "Iniciando backend..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Aguardando backend..."
for i in {1..10}; do
  curl -sf http://localhost:8000/ > /dev/null && break
  sleep 1
done

echo "Iniciando frontend..."
API_URL=http://127.0.0.1:8000/analisar streamlit run app/frontend.py

wait $BACKEND_PID