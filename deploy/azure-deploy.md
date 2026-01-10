# Azure App Service Deployment Guide

Deploy ProjectData to Azure using GitHub integration (no CLI required).

---

## Prerequisites

- **Azure Account** with active subscription (free tier works!)
- **GitHub Account** with your repo pushed
- **Gemini API Key** for LLM features

---

## Step 1: Create Azure App Service

1. Go to [Azure Portal](https://portal.azure.com)

2. Click **Create a resource** → Search **"Web App"** → Click **Create**

3. **Basics Tab**:
   | Setting | Value |
   |---------|-------|
   | Subscription | Your subscription |
   | Resource Group | Create new: `projectdata-rg` |
   | Name | `projectdata` (URL: projectdata.azurewebsites.net) |
   | Publish | **Docker Container** |
   | Operating System | **Linux** |
   | Region | Choose closest to you |
   | Pricing Plan | **Free F1** or **Basic B1** |

4. **Docker Tab**:
   | Setting | Value |
   |---------|-------|
   | Options | Single Container |
   | Image Source | **GitHub Actions** |

5. Click **Review + create** → **Create**

---

## Step 2: Connect GitHub Repository

1. In your App Service, go to **Deployment Center**

2. **Source**: Select **GitHub**

3. **Authorize** Azure to access your GitHub

4. Configure:
   | Setting | Value |
   |---------|-------|
   | Organization | Your GitHub username |
   | Repository | `ProjectData` |
   | Branch | `test/code-review-demo` or `main` |

5. **Build Provider**: Select **GitHub Actions**

6. Click **Save** - Azure will create a workflow file in your repo

---

## Step 3: Configure Environment Variables

1. Go to **Configuration** → **Application settings**

2. Click **+ New application setting** for each:

   | Name | Value |
   |------|-------|
   | `GEMINI_API_KEY` | your-gemini-api-key |
   | `LLM_PROVIDER` | gemini |
   | `NODE_ENV` | production |
   | `PORT` | 8080 |
   | `WEBSITES_PORT` | 8080 |

3. Click **Save** → **Continue** to restart

---

## Step 4: Wait for Deployment

- GitHub Actions will build and deploy automatically
- Check progress at: **Deployment Center** → **Logs**
- First build takes ~10-15 minutes

---

## Step 5: Access Your App

Your app URL:
```
https://projectdata.azurewebsites.net
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Build fails | Check GitHub Actions logs in your repo |
| App crashes | Go to **Log stream** in Azure portal |
| Memory issues | Upgrade to B1 plan ($13/month) |
| Container not starting | Verify `WEBSITES_PORT=8080` is set |

---

## Cost Estimate

| Plan | Monthly Cost |
|------|--------------|
| Free F1 | $0 (60 min/day limit) |
| Basic B1 | ~$13/month |
| Standard S1 | ~$70/month |

---

## Quick Reference

- **Portal**: [portal.azure.com](https://portal.azure.com)
- **App URL**: https://projectdata.azurewebsites.net
- **Logs**: App Service → Log stream
- **Restart**: App Service → Overview → Restart
