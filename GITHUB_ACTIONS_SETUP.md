# GitHub Actions Setup Guide

## 🚀 Build Windows .exe Automatically

This guide shows you how to use GitHub Actions to build a standalone Windows .exe **without needing a Windows PC**.

---

## ✅ What's Ready

I've created:
- ✅ `.github/workflows/build-windows-exe.yml` - GitHub Actions workflow
- ✅ `.gitignore` - Prevents committing build artifacts
- ✅ `myracingdata.spec` - PyInstaller configuration

---

## 📝 Step-by-Step Instructions

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `myracingdata-telemetry` (or any name)
3. Choose **Public** or **Private**
4. Click **Create repository**

### Step 2: Push Code to GitHub

```bash
cd myracingdata-telemetry-capture

# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - MyRacingData Telemetry Capture v1.0.0"

# Add GitHub remote (replace YOUR_USERNAME and YOUR_REPO)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push
git push -u origin main
```

If it says "main" doesn't exist, try:
```bash
git branch -M main
git push -u origin main
```

### Step 3: Trigger Build

The build will start automatically when you push!

**OR manually trigger:**
1. Go to your repo on GitHub
2. Click **Actions** tab
3. Click **Build Windows Executable** workflow
4. Click **Run workflow** button
5. Click green **Run workflow** button

### Step 4: Wait for Build

- Build takes **5-10 minutes**
- You'll see a yellow dot 🟡 (running) → green check ✅ (success)

### Step 5: Download .exe

1. Click on the completed workflow run
2. Scroll down to **Artifacts** section
3. Download:
   - `MyRacingData-Telemetry-Windows-Executable` (just the .exe)
   - `MyRacingData-Telemetry-Windows-Package` (complete ZIP with README)

---

## 🎯 What You Get

After build completes:

```
MyRacingData-Telemetry-Windows-Package.zip
├── MyRacingData-Telemetry.exe    (~15 MB, standalone)
├── README.txt                     (instructions)
└── config.ini.example             (configuration template)
```

**The .exe requires NO Python installation!** ✅

---

## 🔄 Automatic Builds

The workflow triggers on:
- ✅ Push to `main` or `master` branch
- ✅ Pull requests
- ✅ Manual trigger (workflow_dispatch)
- ✅ Git tags starting with `v` (creates release)

---

## 📦 Creating a Release

To create an official release:

```bash
# Tag version
git tag -a v1.0.0 -m "Release v1.0.0"

# Push tag
git push origin v1.0.0
```

GitHub Actions will:
1. Build the .exe
2. Create a GitHub Release
3. Attach the .exe and ZIP to the release

---

## 🔧 Customization

### Change Version Number

Edit `.github/workflows/build-windows-exe.yml`, line 49:
```yaml
DestinationPath MyRacingData-Telemetry-v1.0.0-Windows.zip
```

### Build on Different Events

Edit the `on:` section:
```yaml
on:
  push:
    branches: [ main ]
  # Add more triggers here
```

---

## 🐛 Troubleshooting

### Build Fails

1. Click on the failed workflow
2. Click on the failed job
3. Expand the failed step
4. Read error message

Common issues:
- **Missing dependencies**: Add to `requirements.txt`
- **Import errors**: Make sure all imports are in `src/`
- **Permission errors**: Check file paths

### Can't Push to GitHub

```bash
# Set up authentication
git config --global user.email "you@example.com"
git config --global user.name "Your Name"

# Use personal access token for HTTPS
# Or set up SSH keys
```

### Workflow Doesn't Trigger

- Check you pushed to `main` or `master` branch
- Check Actions is enabled in repo settings
- Try manual trigger from Actions tab

---

## 💡 Pro Tips

1. **Keep Secrets Safe**: Never commit API keys
2. **Test Locally First**: Build on Windows first if possible
3. **Version Your Releases**: Use git tags (v1.0.0, v1.1.0, etc.)
4. **Check Artifacts**: Download and test before sharing

---

## 📊 Build Status Badge

Add to your README.md:

```markdown
![Build Status](https://github.com/YOUR_USERNAME/YOUR_REPO/workflows/Build%20Windows%20Executable/badge.svg)
```

---

## ✅ Summary

1. **Create GitHub repo** (2 minutes)
2. **Push code** (1 minute)
3. **Wait for build** (5-10 minutes)
4. **Download .exe** (1 minute)

**Total time**: ~15 minutes
**Cost**: FREE
**Result**: Standalone Windows .exe with no Python requirement!

---

## 🎉 Next Steps

After you have the .exe:

1. **Test it** on Windows (double-click should work)
2. **Share it** with users
3. **Create releases** for version tracking
4. **Set up auto-updates** (optional, advanced)

---

## 📞 Need Help?

If something doesn't work:
1. Check the workflow logs on GitHub
2. Read the error messages
3. Google the error
4. Check PyInstaller documentation

---

**Ready to build! Just push to GitHub and Actions will do the rest!** 🚀
