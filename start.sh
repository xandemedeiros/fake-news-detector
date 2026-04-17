#!/bin/bash

trap "kill 0" EXIT

echo "Iniciando o Detector de Fake News..."
echo "================================="

echo "Ligando o Backend..."
uvicorn app.main:app --reload &

sleep 3

echo "Ligando o Frontend..."
streamlit run app/frontend.py