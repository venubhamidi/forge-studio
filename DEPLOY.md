# Deploy Forge Studio to Railway

## Prerequisites

- Railway account (https://railway.app)
- MCP Gateway already deployed (get the URL)
- Bearer token from MCP Gateway

## Deploy via Railway Dashboard

### Step 1: Create New Service

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Connect your GitHub account
4. Select the **forge-studio** repository
5. Railway will auto-detect the Dockerfile

### Step 2: Configure Environment Variables

In Railway dashboard → **Variables** tab, add:

| Variable | Value | Required | Notes |
|----------|-------|----------|-------|
| `GATEWAY_URL` | `https://your-gateway.up.railway.app` | Yes | Full URL of your MCP Gateway |
| `BEARER_TOKEN` | `eyJhbGc...` | No | Optional - pre-fills token in UI |

**Note:** The bearer token is optional. If not set, users will need to paste it manually in the UI.

### Step 3: Configure Settings

1. Go to **Settings** tab
2. **Service Name**: `forge-studio` (or custom name)
3. **Region**: Choose closest to your users
4. **Health Check**: Leave default (Railway auto-detects Streamlit)

### Step 4: Deploy

1. Click "Deploy" in the dashboard
2. Wait for build to complete (~2-3 minutes)
3. Once deployed, Railway provides a public URL like:
   - `https://forge-studio.up.railway.app`

### Step 5: Access Forge Studio

1. Open the Railway-provided URL
2. Login with credentials:
   - **Username**: `admin`
   - **Password**: `Alekhya0516@654321`
3. Upload OpenAPI specs and register them as MCP tools

## Option 2: Deploy via Railway CLI

```bash
# Login to Railway
railway login

# Create new project or link existing
railway init

# Set environment variables
railway variables set GATEWAY_URL=https://your-gateway.up.railway.app
railway variables set BEARER_TOKEN=your-bearer-token-here

# Deploy
railway up

# Get the URL
railway domain
```

## Option 3: Deploy from Subdirectory

If deploying from the parent AgenticAI directory:

1. In Railway dashboard → Settings → Build
2. Set "Root Directory" to: `streamlit-ui`
3. Keep "Dockerfile Path" as: `Dockerfile`

## Getting the Bearer Token

If you don't have the bearer token yet:

```bash
# Run this locally (replace YOUR_SECRET with gateway's JWT_SECRET_KEY)
docker run --rm -i ghcr.io/ibm/mcp-context-forge:0.8.0 \
  python3 -m mcpgateway.utils.create_jwt_token \
  --username admin \
  --exp 0 \
  --secret YOUR_SECRET
```

Or get it from your gateway deployment logs.

## After Deployment

### Access Your UI

- **Public URL**: `https://<your-ui>.up.railway.app`

### Test the Deployment

1. Open the URL in your browser
2. Verify the gateway URL is correct in the sidebar
3. Bearer token should be pre-filled (if set as env var)
4. Try uploading a sample OpenAPI spec

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GATEWAY_URL` | Yes | `http://gateway:4444` | URL of your MCP Gateway |
| `BEARER_TOKEN` | Recommended | - | Pre-fill the bearer token (can also paste in UI) |

## Connecting Gateway and UI

Both services should be deployed as **separate Railway projects**:

```
┌─────────────────────────┐
│  Project 1: Gateway     │
│  URL: gateway.railway   │
│  + PostgreSQL plugin    │
└─────────────────────────┘
            ↑
            │ HTTPS
            │
┌─────────────────────────┐
│  Project 2: UI          │
│  URL: ui.railway        │
│  GATEWAY_URL → above    │
└─────────────────────────┘
```

## Alternative: Same Project, Multiple Services

You can also deploy both in one Railway project:

1. Create one project
2. Add PostgreSQL database
3. Add service 1: Gateway (from `/mcp-gateway`)
4. Add service 2: UI (from `/streamlit-ui`)
5. Set UI's `GATEWAY_URL` to gateway's **private** URL: `http://gateway.railway.internal:4444`

This keeps traffic internal within Railway's network.

## Security Best Practices

1. **Use HTTPS**: Railway provides this automatically
2. **Don't commit tokens**: Use environment variables
3. **Regenerate tokens**: Periodically update the bearer token
4. **Restrict access**: Consider adding authentication to Streamlit (optional)

## Troubleshooting

### UI Can't Connect to Gateway

- **Check GATEWAY_URL**: Ensure it's the public Railway URL (with `https://`)
- **Verify bearer token**: Token must match the gateway's JWT secret
- **Check gateway logs**: Ensure gateway is accepting requests
- **CORS issues**: Gateway should allow requests from UI domain

### Health Check Fails

- Streamlit health endpoint is `/_stcore/health`
- Railway should auto-detect this
- If needed, manually set in Settings → Health Check Path: `/_stcore/health`
- Check logs if issues persist

### Blank Page / Won't Load

- Check Railway logs for errors
- Verify Dockerfile builds successfully
- Ensure port 8501 is correct (Railway auto-detects)

## Cost Estimate

Railway pricing:
- **Hobby Plan**: $5/month for 500 hours
- Typical usage: ~$5/month for Streamlit UI

**Total for both services**: ~$10-15/month

## Customization

### Adding Authentication

To add password protection to Streamlit:

1. Install `streamlit-authenticator`
2. Add auth logic to `app.py`
3. Rebuild and redeploy

### Custom Domain

1. In Railway dashboard → Settings → Domains
2. Click "Add Domain"
3. Add your custom domain
4. Configure DNS records as shown

## Next Steps

After deployment:
1. Access your UI at the Railway URL
2. Upload OpenAPI specs
3. Register APIs as MCP tools
4. Share the MCP endpoints with your AI applications
5. Monitor usage in Railway dashboard

## Support

- **Railway Docs**: https://docs.railway.app
- **Streamlit Docs**: https://docs.streamlit.io
- **MCP Context Forge**: https://github.com/IBM/mcp-context-forge
