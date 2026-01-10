# AWS App Runner Deployment Guide (Console)

Deploy ProjectData to AWS App Runner using the AWS Console (no CLI required).

---

## Prerequisites

- **AWS Account** with billing enabled
- **Docker Desktop** installed locally
- **Gemini API Key** for LLM features

---

## Step 1: Push Code to GitHub

AWS App Runner can deploy directly from GitHub. Push your code:

```powershell
cd C:\Users\4236h\ProjectData
git add .
git commit -m "Add Docker configuration for AWS deployment"
git push origin main
```

---

## Step 2: Create AWS App Runner Service

1. **Go to AWS Console**: [console.aws.amazon.com](https://console.aws.amazon.com)

2. **Navigate to App Runner**: Search for "App Runner" in the search bar

3. **Create Service** → Click "Create service"

4. **Source Configuration**:
   - Source type: **Source code repository**
   - Connect to GitHub (authorize AWS if first time)
   - Select your repository: `ProjectData`
   - Branch: `main`

5. **Deployment Settings**:
   - Deployment trigger: **Automatic** (deploys on each push)
   - Source directory: `/` (root)

6. **Build Settings** → Choose **Configure all settings here**:
   ```
   Runtime: Docker
   Build command: (leave empty - uses Dockerfile)
   Start command: (leave empty - uses Dockerfile CMD)
   Port: 8080
   ```

7. **Service Settings**:
   - Service name: `projectdata`
   - CPU: 1 vCPU
   - Memory: 2 GB (minimum for Python ML dependencies)

8. **Environment Variables** → Add:
   | Key | Value |
   |-----|-------|
   | `NODE_ENV` | `production` |
   | `PORT` | `8080` |
   | `GEMINI_API_KEY` | `your-gemini-api-key` |
   | `LLM_PROVIDER` | `gemini` |
   | `FRONTEND_URL` | `https://projectdata.xxx.awsapprunner.com` |

9. **Click "Create & deploy"**

---

## Step 3: Wait for Deployment

- Build takes ~10-15 minutes (Python dependencies are large)
- Monitor progress in the App Runner console
- Once status shows "Running", your app is live!

---

## Step 4: Access Your App

Your app URL will be:
```
https://projectdata-xxxxx.region.awsapprunner.com
```

The URL will contain "projectdata" as you requested!

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Build fails | Check Docker build logs in App Runner console |
| Memory errors | Increase memory to 3-4 GB |
| LLM not working | Verify GEMINI_API_KEY is set correctly |
| CORS errors | Update FRONTEND_URL env variable |

---

## Estimated Costs

| Resource | Monthly Cost |
|----------|--------------|
| App Runner (1 vCPU, 2GB) | ~$15-25/month |
| Data transfer | ~$1-5/month |

*Free tier: 100 build minutes/month*

---

## Alternative: Local Docker Test First

Before deploying to AWS, test locally:

```powershell
# Set your Gemini key
$env:GEMINI_API_KEY = "your-key-here"

# Build and run
docker-compose up --build

# Access at http://localhost:8080
```
