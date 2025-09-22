# Float Chat AI Project Setup Script (PowerShell)
# Run: .\setup.ps1

$base = "float-chat-ai"

# Define folders
$folders = @(
    "$base/backend/app/services",
    "$base/backend/tests",
    "$base/frontend/public",
    "$base/frontend/src/components",
    "$base/data/embeddings"
)

# Create folders
foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
}

# Create backend files
New-Item "$base/backend/app/main.py" -ItemType File -Force | Out-Null
New-Item "$base/backend/app/db.py" -ItemType File -Force | Out-Null
New-Item "$base/backend/app/__init__.py" -ItemType File -Force | Out-Null
New-Item "$base/backend/app/services/argo_data.py" -ItemType File -Force | Out-Null
New-Item "$base/backend/app/services/ai_engine.py" -ItemType File -Force | Out-Null
New-Item "$base/backend/app/services/utils.py" -ItemType File -Force | Out-Null
New-Item "$base/backend/tests/test_api.py" -ItemType File -Force | Out-Null
New-Item "$base/backend/requirements.txt" -ItemType File -Force | Out-Null
New-Item "$base/backend/Dockerfile" -ItemType File -Force | Out-Null
New-Item "$base/backend/uvicorn.sh" -ItemType File -Force | Out-Null

# Create frontend files
New-Item "$base/frontend/public/index.html" -ItemType File -Force | Out-Null
New-Item "$base/frontend/src/App.js" -ItemType File -Force | Out-Null
New-Item "$base/frontend/src/styles.css" -ItemType File -Force | Out-Null
New-Item "$base/frontend/package.json" -ItemType File -Force | Out-Null
New-Item "$base/frontend/Dockerfile" -ItemType File -Force | Out-Null

# Create data files
New-Item "$base/data/sample_argo.nc" -ItemType File -Force | Out-Null
New-Item "$base/data/queries.sql" -ItemType File -Force | Out-Null

# Root files
New-Item "$base/docker-compose.yml" -ItemType File -Force | Out-Null
New-Item "$base/README.md" -ItemType File -Force | Out-Null
New-Item "$base/.env" -ItemType File -Force | Out-Null

Write-Host "✅ Project structure created successfully at $base"
