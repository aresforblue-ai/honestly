# 🚀 Cloudflare Pages Deployment Guide

This guide explains how to deploy the **conductme** application to Cloudflare Pages from the **honestly** repository.

## 📋 Overview

The **honestly** repository contains multiple components:
- **conductme/** - Next.js frontend application (the web app to deploy)
- **backend-python/** - Python backend services
- **backend-solana/** - Solana blockchain programs
- And other components

For Cloudflare Pages deployment, we're deploying **only the conductme Next.js app**.

## 🔧 Build Configuration

### Package.json (Root)
The root `package.json` has a build script that delegates to conductme:

```json
{
  "scripts": {
    "build": "cd conductme && npm install && npm run build"
  }
}
```

### Wrangler.toml Configuration
The `wrangler.toml` file is configured for Cloudflare Pages:

```toml
name = "veridicus"
compatibility_date = "2024-01-01"

[env.production]
name = "veridicus"
compatibility_date = "2024-01-01"

# Build configuration for Cloudflare Pages
# The build command should be: npm install && npm run build
# This will run the build script in root package.json which delegates to conductme/
# Output directory: conductme/.next

pages_build_output_dir = "conductme/.next"
```

## ⚙️ Cloudflare Pages Settings

When setting up your Cloudflare Pages project, use these settings:

### Framework Preset
- **Framework**: Next.js

### Build Settings
- **Build command**: `npm install && npm run build`
- **Build output directory**: `conductme/.next`

### Environment Variables (Optional)
Add any required environment variables in the Cloudflare Pages dashboard under Settings → Environment variables.

## 🛠️ How It Works

1. Cloudflare Pages clones the **honestly** repository
2. Runs `npm install` in the root (installs root dependencies)
3. Runs `npm run build` in the root
4. The build script changes to `conductme/` directory
5. Installs conductme dependencies with `npm install`
6. Builds the Next.js app with `npm run build`
7. Next.js outputs to `conductme/.next/`
8. Cloudflare Pages uses `conductme/.next/` as the deployment directory

## 🚨 Troubleshooting

### Error: "Could not read package.json"
**Cause**: Build command is running in wrong directory.
**Solution**: Ensure build command is `npm install && npm run build` (not `cd conductme && npm install && npm run build`)

### Error: "No build script found"
**Cause**: Missing build script in root package.json.
**Solution**: Verify root package.json contains the build script shown above.

### Error: "Build output directory not found"
**Cause**: Incorrect output directory configuration.
**Solution**: Set build output directory to `conductme/.next` (not just `.next`)

### Error: "npm ci requires package-lock.json"
**Cause**: Cloudflare auto-detects and runs `npm ci` which requires synchronized package.json and package-lock.json.
**Solution**: Ensure `conductme/package-lock.json` is committed and up-to-date. Run `npm install` in conductme/ to regenerate if needed.

## 📝 Local Testing

To test the build locally:

```bash
# From repository root
npm run build

# The output will be in conductme/.next/
ls -la conductme/.next/
```

## 🔗 Related Documentation

- [Conductme Deployment Guide](./conductme/DEPLOYMENT.md) - Complete deployment guide
- [Cloudflare Pages Docs](https://developers.cloudflare.com/pages/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)

## 🎯 Next Steps

After deployment:
1. Verify the site loads at your Cloudflare Pages URL
2. Configure custom domain (veridicus.io) in Cloudflare Pages settings
3. Set up environment variables if needed
4. Configure any required API endpoints

## 💡 Tips

- The build takes approximately 2-5 minutes on Cloudflare Pages
- Cloudflare automatically installs Node.js and npm
- You can monitor build logs in the Cloudflare Pages dashboard
- Each git push to your main branch triggers an automatic deployment
- Preview deployments are created for pull requests

## 🔐 Security Note

- Never commit secrets or API keys to the repository
- Use Cloudflare Pages environment variables for sensitive data
- Ensure `.env.local` is in `.gitignore` (it is by default)

---

**Last Updated**: December 2024
**Repository**: [veridicusio/honestly](https://github.com/veridicusio/honestly)
