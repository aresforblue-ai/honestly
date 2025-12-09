# 🚀 Deploy VERIDICUS to Cloudflare Pages - Windows Command Line Guide

**Skip the web interface! Deploy from your terminal instead.**

---

## Prerequisites

1. **Install Node.js** (if not already installed)
   - Download from: https://nodejs.org/
   - Or check if installed: `node --version`

2. **Install Wrangler CLI** (Cloudflare's command line tool)
   ```powershell
   npm install -g wrangler
   ```

3. **Login to Cloudflare**
   ```powershell
   wrangler login
   ```
   - This will open your browser to authorize
   - Click "Allow" in the browser

---

## Step 1: Navigate to Your Project

```powershell
cd C:\Users\tyler\honestly-1\conductme
```

---

## Step 2: Install Dependencies Locally

```powershell
npm install
```

**This will:**
- Install all packages
- Update `package-lock.json` to match `package.json`
- Fix any sync issues

---

## Step 3: Test Build Locally

```powershell
npm run build
```

**If this works**, you're ready to deploy!  
**If it fails**, fix the errors first before deploying.

---

## Step 4: Initialize Cloudflare Pages Project

```powershell
wrangler pages project create veridicus
```

**This will:**
- Create a new Pages project called "veridicus"
- Give you a project ID (save this!)

---

## Step 5: Deploy to Cloudflare Pages

### Option A: Deploy from Local Build (Easiest)

```powershell
# Build first
npm run build

# Deploy the .next folder
wrangler pages deploy .next --project-name=veridicus
```

### Option B: Deploy from Git (Automatic)

```powershell
# Connect your Git repository
wrangler pages project create veridicus --production-branch=main

# This will prompt you to connect GitHub
# Follow the prompts to authorize
```

---

## Step 6: Set Environment Variables

```powershell
# Set production environment variables
wrangler pages secret put NEXT_PUBLIC_API_URL --project-name=veridicus
# When prompted, enter: https://api.veridicus.io

wrangler pages secret put NEXT_PUBLIC_WS_URL --project-name=veridicus
# When prompted, enter: wss://ws.veridicus.io/ws/veridicus

wrangler pages secret put NEXT_PUBLIC_SITE_URL --project-name=veridicus
# When prompted, enter: https://veridicus.io
```

**Note:** For Pages, you might need to use the dashboard for environment variables instead:
- Go to: https://dash.cloudflare.com → Workers & Pages → veridicus → Settings → Environment Variables

---

## Step 7: Connect Custom Domain

```powershell
# Add your custom domain
wrangler pages domain add veridicus.io --project-name=veridicus
```

**Or use the dashboard:**
- Go to your Pages project → Custom domains → Add domain
- Enter: `veridicus.io`

---

## Alternative: Deploy Using Git Integration (Recommended)

This is the easiest way - Cloudflare will auto-deploy on every push:

```powershell
# 1. Make sure your code is pushed to GitHub
cd C:\Users\tyler\honestly-1
git add .
git commit -m "Ready for Cloudflare Pages deployment"
git push

# 2. Create Pages project connected to Git
wrangler pages project create veridicus --production-branch=main

# 3. Follow the prompts to:
#    - Connect your GitHub account
#    - Select repository: veridicusio/honestly
#    - Set build command: cd conductme && npm install && npm run build
#    - Set output directory: .next
#    - Set root directory: conductme
```

---

## Quick Deploy Script

Create a file `deploy.ps1` in your `conductme` folder:

```powershell
# deploy.ps1
Write-Host "Building project..." -ForegroundColor Green
npm run build

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build successful! Deploying..." -ForegroundColor Green
    wrangler pages deploy .next --project-name=veridicus
} else {
    Write-Host "Build failed! Fix errors first." -ForegroundColor Red
}
```

**Run it:**
```powershell
.\deploy.ps1
```

---

## Troubleshooting

### "wrangler: command not found"
```powershell
npm install -g wrangler
```

### "Not logged in"
```powershell
wrangler login
```

### "Build failed"
```powershell
# Fix dependencies first
npm install
npm run build
```

### "Project not found"
```powershell
# List your projects
wrangler pages project list

# Or create a new one
wrangler pages project create veridicus
```

### "Permission denied" or PowerShell execution policy
```powershell
# Allow scripts to run (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Useful Commands

```powershell
# List all Pages projects
wrangler pages project list

# View project details
wrangler pages project get veridicus

# View deployments
wrangler pages deployment list --project-name=veridicus

# View deployment details
wrangler pages deployment tail --project-name=veridicus

# Delete a project (careful!)
wrangler pages project delete veridicus
```

---

## Full Workflow Example

```powershell
# 1. Navigate to project
cd C:\Users\tyler\honestly-1\conductme

# 2. Install/update dependencies
npm install

# 3. Test build locally
npm run build

# 4. Deploy to Cloudflare Pages
wrangler pages deploy .next --project-name=veridicus

# 5. Check deployment status
wrangler pages deployment list --project-name=veridicus
```

---

## Next Steps After Deployment

1. **Set environment variables** in Cloudflare dashboard
2. **Connect custom domain** `veridicus.io`
3. **Test the site** at the provided `.pages.dev` URL
4. **Set up auto-deploy** from Git (recommended)

---

## Why This is Better Than Web Interface

✅ **Faster** - No clicking through menus  
✅ **Repeatable** - Same commands every time  
✅ **Scriptable** - Can automate deployments  
✅ **Less confusing** - No Workers vs Pages confusion  
✅ **Better for CI/CD** - Can integrate with GitHub Actions

---

**That's it!** Your app should be live in minutes. 🎉

