#!/bin/bash

# Nombre del repositorio
REPO_NAME="aula-virtual"
GITHUB_USER="orlandoj123"

echo "🚀 Inicializando repositorio GitHub..."

# Inicializar git en la carpeta actual
git init

# Agregar todos los archivos
git add .

# Commit inicial
git commit -m "Inicial: Plataforma Aula Virtual con autenticación, BD y Google Drive"

# Agregar remote
git remote add origin git@github.com:${GITHUB_USER}/${REPO_NAME}.git

# Crear rama main
git branch -M main

# Subir a GitHub
git push -u origin main

echo "✅ Repositorio creado en: https://github.com/${GITHUB_USER}/${REPO_NAME}"
