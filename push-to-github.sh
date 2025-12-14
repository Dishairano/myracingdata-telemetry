#!/bin/bash
# Automated GitHub push script for MyRacingData Telemetry

echo "🚀 MyRacingData Telemetry - GitHub Push Script"
echo "=============================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed!"
    echo "   Install: sudo apt install git"
    exit 1
fi

echo "✓ Git installed: $(git --version)"
echo ""

# Get GitHub username
echo "📝 GitHub Setup"
echo "==============="
read -p "Enter your GitHub username: " GITHUB_USER

if [ -z "$GITHUB_USER" ]; then
    echo "❌ Username cannot be empty"
    exit 1
fi

# Get repository name
read -p "Enter repository name (default: myracingdata-telemetry): " REPO_NAME
REPO_NAME=${REPO_NAME:-myracingdata-telemetry}

echo ""
echo "📋 Configuration:"
echo "   Username: $GITHUB_USER"
echo "   Repo: $REPO_NAME"
echo "   URL: https://github.com/$GITHUB_USER/$REPO_NAME"
echo ""

read -p "Is this correct? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "❌ Cancelled"
    exit 1
fi

# Initialize git
echo ""
echo "🔧 Initializing Git repository..."
git init

# Configure git
echo ""
read -p "Enter your email for Git: " GIT_EMAIL
git config user.email "$GIT_EMAIL"
git config user.name "$GITHUB_USER"

echo "✓ Git configured"

# Add all files
echo ""
echo "📦 Adding files..."
git add .

# Commit
echo ""
echo "💾 Creating commit..."
git commit -m "Initial commit - MyRacingData Telemetry Capture v1.0.0

Features:
- Assetto Corsa support (~150 data points)
- Le Mans Ultimate support (~200 data points)
- 60Hz real-time streaming
- System tray application
- Auto-detection
- WebSocket streaming to MyRacingData platform

Build:
- GitHub Actions workflow for Windows .exe
- PyInstaller configuration
- Complete documentation"

echo "✓ Commit created"

# Add remote
echo ""
echo "🔗 Adding GitHub remote..."
git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"

echo "✓ Remote added"

# Rename branch to main
echo ""
echo "🌿 Setting up main branch..."
git branch -M main

# Push
echo ""
echo "🚀 Pushing to GitHub..."
echo ""
echo "⚠️  You'll need to authenticate with GitHub"
echo "   Use your GitHub password or Personal Access Token"
echo ""
echo "   To create a token:"
echo "   1. Go to: https://github.com/settings/tokens"
echo "   2. Click: Generate new token (classic)"
echo "   3. Select: repo (full control)"
echo "   4. Generate and copy the token"
echo "   5. Use the token as your password"
echo ""

read -p "Press Enter when ready to push..."

git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Success! Code pushed to GitHub"
    echo ""
    echo "🎉 Next Steps:"
    echo "   1. Go to: https://github.com/$GITHUB_USER/$REPO_NAME"
    echo "   2. Click 'Actions' tab"
    echo "   3. Watch the build (takes 5-10 minutes)"
    echo "   4. Download the .exe artifact when done"
    echo ""
    echo "📦 The Windows .exe will be available for download!"
else
    echo ""
    echo "❌ Push failed"
    echo ""
    echo "Common issues:"
    echo "   1. Repository doesn't exist - Create it at: https://github.com/new"
    echo "   2. Authentication failed - Use Personal Access Token"
    echo "   3. Wrong credentials - Check username and token"
    echo ""
    echo "To try again: ./push-to-github.sh"
fi
