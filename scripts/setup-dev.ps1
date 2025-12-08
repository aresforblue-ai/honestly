# ============================================
# HONESTLY DEVELOPER SETUP SCRIPT (WINDOWS)
# ============================================
# Run this script to set up your development environment
# Usage: .\scripts\setup-dev.ps1

param(
    [switch]$SkipDocker,
    [switch]$SkipPython,
    [switch]$SkipNode,
    [switch]$SkipZKP
)

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  HONESTLY TRUTH ENGINE - DEV SETUP" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check prerequisites
Write-Host "[1/7] Checking prerequisites..." -ForegroundColor Yellow

# Check Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Git is not installed" -ForegroundColor Red
    exit 1
}
Write-Host "  Git: $(git --version)" -ForegroundColor Green

# Check Node.js
if (-not $SkipNode) {
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Host "  Node.js: Not found - please install from https://nodejs.org/" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Node.js: $(node --version)" -ForegroundColor Green
}

# Check Python
if (-not $SkipPython) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "  Python: Not found - please install from https://python.org/" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Python: $(python --version)" -ForegroundColor Green
}

# Check Docker
if (-not $SkipDocker) {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Host "  Docker: $(docker --version)" -ForegroundColor Green
    } else {
        Write-Host "  Docker: Not found (optional for local dev)" -ForegroundColor Yellow
    }
}

# Create virtual environment
if (-not $SkipPython) {
    Write-Host "`n[2/7] Setting up Python virtual environment..." -ForegroundColor Yellow
    
    if (-not (Test-Path "venv")) {
        python -m venv venv
        Write-Host "  Created virtual environment" -ForegroundColor Green
    } else {
        Write-Host "  Virtual environment already exists" -ForegroundColor Green
    }
    
    # Activate and install dependencies
    & .\venv\Scripts\Activate.ps1
    pip install --upgrade pip | Out-Null
    pip install -r backend-python/requirements.txt
    pip install pytest pytest-cov httpx ruff black pre-commit
    Write-Host "  Python dependencies installed" -ForegroundColor Green
}

# Install Node.js dependencies
if (-not $SkipNode) {
    Write-Host "`n[3/7] Installing Node.js dependencies..." -ForegroundColor Yellow
    
    # Root package
    if (Test-Path "package.json") {
        npm install
    }
    
    # Frontend
    if (Test-Path "frontend-app/package.json") {
        Push-Location frontend-app
        npm install
        Pop-Location
        Write-Host "  Frontend dependencies installed" -ForegroundColor Green
    }
    
    # ConductMe
    if (Test-Path "conductme/package.json") {
        Push-Location conductme
        npm install
        Pop-Location
        Push-Location conductme/core
        npm install
        Pop-Location
        Write-Host "  ConductMe dependencies installed" -ForegroundColor Green
    }
}

# Setup ZKP
if (-not $SkipZKP) {
    Write-Host "`n[4/7] Setting up ZKP environment..." -ForegroundColor Yellow
    
    Push-Location backend-python/zkp
    npm install
    
    # Create artifacts directories
    $dirs = @(
        "artifacts/common",
        "artifacts/age",
        "artifacts/authenticity",
        "artifacts/age_level3",
        "artifacts/level3_inequality"
    )
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    # Check if ptau exists
    if (-not (Test-Path "artifacts/common/pot16_final.ptau")) {
        Write-Host "  Downloading Powers of Tau (this may take a few minutes)..." -ForegroundColor Yellow
        $ptauUrl = "https://storage.googleapis.com/zkevm/ptau/powersOfTau28_hez_final_16.ptau"
        Start-BitsTransfer -Source $ptauUrl -Destination "artifacts/common/pot16_final.ptau" -ErrorAction SilentlyContinue
        if (-not $?) {
            curl.exe -L $ptauUrl -o "artifacts/common/pot16_final.ptau"
        }
    }
    Write-Host "  ZKP environment ready" -ForegroundColor Green
    Pop-Location
}

# Setup environment file
Write-Host "`n[5/7] Setting up environment configuration..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Host "  Created .env from env.example" -ForegroundColor Green
        Write-Host "  IMPORTANT: Review and customize .env before starting services" -ForegroundColor Yellow
    }
} else {
    Write-Host "  .env already exists" -ForegroundColor Green
}

# Setup pre-commit hooks
Write-Host "`n[6/7] Setting up pre-commit hooks..." -ForegroundColor Yellow

if (Get-Command pre-commit -ErrorAction SilentlyContinue) {
    pre-commit install
    Write-Host "  Pre-commit hooks installed" -ForegroundColor Green
} else {
    Write-Host "  Pre-commit not found - skipping hooks setup" -ForegroundColor Yellow
    Write-Host "  Run 'pip install pre-commit && pre-commit install' to enable" -ForegroundColor Yellow
}

# Final setup
Write-Host "`n[7/7] Final setup..." -ForegroundColor Yellow

# Set recommended environment variables
$env:NODE_OPTIONS = "--max-old-space-size=4096"
Write-Host "  NODE_OPTIONS set to --max-old-space-size=4096" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review and customize .env file"
Write-Host "  2. Start Neo4j: docker-compose up neo4j"
Write-Host "  3. Start backend: cd backend-python && python -m uvicorn api.app:app --reload"
Write-Host "  4. Start frontend: cd frontend-app && npm run dev"
Write-Host "  5. Visit http://localhost:5173"
Write-Host ""
Write-Host "For ZKP development:"
Write-Host "  cd backend-python/zkp"
Write-Host "  npm run build:age   # Compile age circuit"
Write-Host "  npm run setup:age   # Generate proving key"
Write-Host "  npm run vk:age      # Export verification key"
Write-Host ""


