# 🚀 Easy Setup - Get Windows .exe in 3 Steps

## Step 1: Create GitHub Account (if you don't have one)

Go to https://github.com/join and create a free account.

---

## Step 2: Create Repository

1. Go to https://github.com/new
2. Repository name: `myracingdata-telemetry`
3. Make it **Public**
4. **DO NOT** initialize with README
5. Click **Create repository**

---

## Step 3: Run the Push Script

Just run this command:

```bash
cd myracingdata-telemetry-capture
./push-to-github.sh
```

The script will ask you:
- Your GitHub username
- Repository name (press Enter for default)
- Your email
- Confirm to push

Then it will push everything to GitHub automatically!

---

## Step 4: Get Your .exe

1. Go to your repo: `https://github.com/YOUR_USERNAME/myracingdata-telemetry`
2. Click **Actions** tab
3. Wait 5-10 minutes for build to complete (green checkmark)
4. Click on the completed workflow
5. Scroll down to **Artifacts**
6. Download: **MyRacingData-Telemetry-Windows-Executable**

You now have a standalone .exe that requires NO Python! 🎉

---

## Troubleshooting

### Authentication Failed

You need a Personal Access Token:

1. Go to: https://github.com/settings/tokens
2. Click: **Generate new token (classic)**
3. Give it a name: "MyRacingData"
4. Select scope: **repo** (check the box)
5. Click: **Generate token**
6. **COPY THE TOKEN** (you won't see it again!)
7. Use this token as your password when pushing

### Repository Already Exists

If you've already created the repo, that's fine! The script will work.

### Build Fails on GitHub

Check the Actions logs:
1. Click on the failed workflow
2. Click on the job
3. Read the error message
4. Usually it's a missing dependency - add it to `requirements.txt`

---

## What the Script Does

1. ✅ Initializes git repository
2. ✅ Configures git with your username/email
3. ✅ Adds all files
4. ✅ Creates commit with description
5. ✅ Adds GitHub remote
6. ✅ Pushes to GitHub

Then GitHub Actions automatically:
1. ✅ Builds Windows .exe
2. ✅ Packages with README
3. ✅ Makes it downloadable

---

## Total Time

- Create GitHub repo: 2 minutes
- Run push script: 2 minutes
- Wait for build: 5-10 minutes

**Total: ~15 minutes to get a standalone Windows .exe!**

---

## Alternative: Manual Method

If you prefer to do it manually:

```bash
cd myracingdata-telemetry-capture

# Initialize
git init
git config user.email "you@example.com"
git config user.name "YourName"

# Commit
git add .
git commit -m "MyRacingData Telemetry v1.0.0"

# Push
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

---

**Ready? Just run: `./push-to-github.sh`** 🚀
