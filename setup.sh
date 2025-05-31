#!/bin/bash

# ChatChonk SaaS Setup Script
# "Tame the Chatter. Find the Signal."
#
# This script automates the initial setup for the ChatChonk project,
# including directory structure, virtual environments, dependencies,
# and basic Git configuration.
#
# Author: Rip Jonesy (with Factory AI assistance)
# Version: 1.0.0
# Date: May 29, 2025

# --- Configuration ---
PROJECT_NAME="chatchonk"
PYTHON_VERSION_MAJOR="3"
PYTHON_VERSION_MINOR="11"
NODE_VERSION_MAJOR="18"

# --- Script Setup ---
# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Pipesi_error if any command in a pipeline fails.
set -o pipefail

# --- Colors ---
COLOR_RESET='\033[0m'
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[0;33m'
COLOR_BLUE='\033[0;34m'

# --- Helper Functions ---
print_info() {
    echo -e "${COLOR_BLUE}[INFO] $1${COLOR_RESET}"
}

print_success() {
    echo -e "${COLOR_GREEN}[SUCCESS] $1${COLOR_RESET}"
}

print_warning() {
    echo -e "${COLOR_YELLOW}[WARNING] $1${COLOR_RESET}"
}

print_error() {
    echo -e "${COLOR_RED}[ERROR] $1${COLOR_RESET}" >&2
    exit 1
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 could not be found. Please install $1 and try again."
    fi
    print_success "$1 is available."
}

check_python_version() {
    print_info "Checking Python version..."
    INSTALLED_PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    INSTALLED_PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

    if [ "$INSTALLED_PY_MAJOR" -lt "$PYTHON_VERSION_MAJOR" ] || ([ "$INSTALLED_PY_MAJOR" -eq "$PYTHON_VERSION_MAJOR" ] && [ "$INSTALLED_PY_MINOR" -lt "$PYTHON_VERSION_MINOR" ]); then
        print_error "Python $PYTHON_VERSION_MAJOR.$PYTHON_VERSION_MINOR or higher is required. Found $INSTALLED_PY_MAJOR.$INSTALLED_PY_MINOR."
    fi
    print_success "Python version $INSTALLED_PY_MAJOR.$INSTALLED_PY_MINOR is sufficient."
}

check_node_version() {
    print_info "Checking Node.js version..."
    INSTALLED_NODE_VERSION=$(node -v | cut -d'v' -f2)
    INSTALLED_NODE_MAJOR=$(echo "$INSTALLED_NODE_VERSION" | cut -d'.' -f1)

    if [ "$INSTALLED_NODE_MAJOR" -lt "$NODE_VERSION_MAJOR" ]; then
        print_error "Node.js $NODE_VERSION_MAJOR or higher is required. Found v$INSTALLED_NODE_VERSION."
    fi
    print_success "Node.js version v$INSTALLED_NODE_VERSION is sufficient."
}


# --- Main Setup Logic ---
main() {
    print_info "🚀 Starting ChatChonk Project Setup..."
    print_info "This script will create the project structure and set up initial configurations."

    # 1. Check Prerequisites
    print_info "Step 1: Checking prerequisites..."
    check_command "git"
    check_command "python3"
    check_python_version
    check_command "node"
    check_node_version
    check_command "npm" # or pnpm/yarn if preferred by user later

    # 2. Create Project Directory Structure
    print_info "Step 2: Creating project directory structure..."
    if [ -d "$PROJECT_NAME" ]; then
        print_warning "Project directory '$PROJECT_NAME' already exists."
        read -r -p "Do you want to proceed and potentially overwrite existing configurations? (y/N): " confirm
        if [[ ! "$confirm" =~ ^[yY](es)?$ ]]; then
            print_info "Setup aborted by user."
            exit 0
        fi
    else
        mkdir "$PROJECT_NAME"
        print_success "Created main project directory: $PROJECT_NAME"
    fi
    
    cd "$PROJECT_NAME"

    DIRECTORIES=(
        "backend"
        "backend/app"
        "backend/app/api"
        "backend/app/api/routes"
        "backend/app/core"
        "backend/app/services"
        "backend/app/models"
        "backend/app/db"
        "backend/app/tasks"
        "backend/app/automodel"
        "backend/app/automodel/providers"
        "frontend"
        "frontend/src"
        "frontend/src/app"
        "frontend/src/components"
        "frontend/src/components/ui"
        "frontend/src/lib"
        "frontend/src/hooks"
        "frontend/src/styles"
        "frontend/public"
        "frontend/public/images"
        "frontend/public/logos"
        "frontend/public/icons"
        "templates"
        "scripts"
        "docs"
        "uploads"
        "tmp"
        "exports"
    )

    for dir in "${DIRECTORIES[@]}"; do
        mkdir -p "$dir"
        print_success "Created directory: $PROJECT_NAME/$dir"
    done

    # 3. Initialize Git Repository
    print_info "Step 3: Initializing Git repository..."
    if [ -d ".git" ]; then
        print_warning ".git directory already exists. Skipping git init."
    else
        git init
        print_success "Git repository initialized."
    fi

    # Create .gitignore
    cat << EOF > .gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.Python
*.egg-info/
.env
.venv/
instance/
pip-wheel-metadata/
.pytest_cache/
.mypy_cache/
.ruff_cache/
build/
develop-eggs/
dist/
downloads/
eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg
MANIFEST

# Node.js
node_modules/
.DS_Store
npm-debug.log*
yarn-debug.log*
yarn-error.log*
package-lock.json
yarn.lock
pnpm-lock.yaml
.next/
out/
coverage/
*.env.local
*.env.development.local
*.env.test.local
*.env.production.local

# IDE specific
.vscode/
.idea/
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?

# ChatChonk specific
uploads/
tmp/
exports/
*.sqlite3
*.db

# OS specific
.DS_Store
Thumbs.db
EOF
    print_success "Created .gitignore file."

    # 4. Create Sample .env File
    print_info "Step 4: Creating sample .env file..."
    if [ -f ".env" ]; then
        print_warning ".env file already exists. Skipping creation of sample .env."
    else
        cat << EOF > .env
# ChatChonk Environment Variables
# Please fill in your actual Supabase credentials and API keys.

# ==== Supabase ====
# Replace with your Supabase project URL
SUPABASE_URL="https://your-project-id.supabase.co"
# Replace with your Supabase anonymous key
SUPABASE_ANON_KEY="your-supabase-anon-key"
# Replace with your Supabase service role key (for backend admin operations)
SUPABASE_SERVICE_ROLE_KEY="your-supabase-service-role-key"

# ==== Backend secrets ====
# Generate a strong secret key, e.g., using: openssl rand -hex 32
CHONK_SECRET_KEY="your-strong-secret-key-here"

# ==== AI Provider API Keys ====
# Required for MVP
HUGGINGFACE_API_KEY="hf_your_huggingface_api_key"
# Optional, for future expansion
OPENAI_API_KEY=""
ANTHROPIC_API_KEY=""
MISTRAL_API_KEY=""
DEEPSEEK_API_KEY=""
QWEN_API_KEY=""

# ==== File processing ====
# These are relative to the project root if running locally,
# or absolute paths in production.
UPLOAD_DIR="./uploads"
TEMP_DIR="./tmp"
EXPORT_DIR="./exports"
TEMPLATES_DIR="./templates" # Relative to backend/app or project root based on config

# ==== Application Settings ====
# For backend (FastAPI)
HOST="0.0.0.0"
PORT="8000"
ENVIRONMENT="development" # development, staging, or production
DEBUG="True" # True or False
RELOAD="True" # True or False for Uvicorn

# For frontend (Next.js)
# The Next.js app will run on port 3000 by default
# API calls from frontend will be proxied or made to http://localhost:8000/api
NEXT_PUBLIC_API_URL="http://localhost:8000/api"
ALLOWED_ORIGINS="http://localhost:3000,https://your-production-domain.com"

# === Logging Settings ===
LOG_LEVEL="INFO" # DEBUG, INFO, WARNING, ERROR, CRITICAL
EOF
        print_success "Created sample .env file. Please edit it with your credentials."
    fi

    # 5. Backend Setup
    print_info "Step 5: Setting up backend (FastAPI)..."
    cd "backend"
    if [ -d ".venv" ]; then
        print_warning "Backend virtual environment '.venv' already exists."
    else
        python3 -m venv .venv
        print_success "Created Python virtual environment for backend in $PROJECT_NAME/backend/.venv"
    fi

    print_info "To install backend dependencies, first activate the virtual environment:"
    print_info "  On macOS/Linux: source backend/.venv/bin/activate"
    print_info "  On Windows:     backend\\.venv\\Scripts\\activate"
    print_info "Then run: pip install -r backend/requirements.txt"
    print_warning "Skipping automatic 'pip install' as it requires venv activation which is shell-dependent."
    print_info "A 'requirements.txt' file should be placed in the 'backend' directory."
    # As an alternative, if we want to try installing directly:
    # print_info "Attempting to install backend dependencies..."
    # source .venv/bin/activate && pip install -r requirements.txt && deactivate
    # This is generally not recommended in setup scripts due to shell complexities.
    cd ..

    # 6. Frontend Setup
    print_info "Step 6: Setting up frontend (Next.js)..."
    cd "frontend"
    if [ -d "node_modules" ]; then
        print_warning "Frontend 'node_modules' directory already exists. Skipping 'npm install'."
    else
        print_info "Installing frontend dependencies using npm..."
        if [ -f "package.json" ]; then
            npm install
            print_success "Frontend dependencies installed."
        else
            print_warning "'package.json' not found in frontend directory. Skipping 'npm install'."
            print_info "A 'package.json' file should be placed in the 'frontend' directory."
        fi
    fi
    cd ..

    # 7. Final Instructions
    print_info "Step 7: Final Instructions & Next Steps"
    echo -e "${COLOR_YELLOW}---------------------------------------------------------------------${COLOR_RESET}"
    echo -e "${COLOR_YELLOW}🎉 ChatChonk Project Setup is Nearing Completion! 🎉${COLOR_RESET}"
    echo -e "${COLOR_YELLOW}---------------------------------------------------------------------${COLOR_RESET}"
    echo ""
    print_info "IMPORTANT: Please edit the '.env' file in the '$PROJECT_NAME' directory with your actual Supabase credentials, API keys, and a strong SECRET_KEY."
    echo ""
    print_info "To run the backend:"
    echo "  1. Navigate to the project root: cd $PROJECT_NAME"
    echo "  2. Activate the Python virtual environment:"
    echo "     - macOS/Linux: source backend/.venv/bin/activate"
    echo "     - Windows:     backend\\.venv\\Scripts\\activate"
    echo "  3. Install dependencies (if you haven't already): pip install -r backend/requirements.txt"
    echo "  4. Start the FastAPI server: uvicorn backend.main:app --reload --port 8000"
    echo "     (The backend will be accessible at http://localhost:8000)"
    echo ""
    print_info "To run the frontend:"
    echo "  1. Navigate to the frontend directory: cd $PROJECT_NAME/frontend"
    echo "  2. Install dependencies (if you haven't already and 'package.json' exists): npm install"
    echo "  3. Start the Next.js development server: npm run dev"
    echo "     (The frontend will be accessible at http://localhost:3000)"
    echo ""
    print_info "Make sure your Supabase tables are provisioned as per the project specification."
    print_info "The AutoModel system will use HuggingFace as the MVP provider. Ensure HUGGINGFACE_API_KEY is set."
    echo ""
    print_success "ChatChonk setup script finished successfully!"
    print_info "Happy Chonking! 🐱‍💻"
}

# --- Execute Main Function ---
main

exit 0
