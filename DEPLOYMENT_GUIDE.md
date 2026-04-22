# Academic Hub - Free Deployment Guide

## Quick Start (Railway + Vercel)

### 1. Prepare Your Code

```bash
# Create deployment configs (already done)
mkdir -p deploy/railway deploy/vercel
```

### 2. Deploy Backend to Railway

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub
   - Get $5/month free credit

2. **Create New Project**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login
   railway login
   
   # Create project
   railway init
   railway up
   ```

3. **Set Environment Variables**
   ```bash
   # Set these in Railway dashboard
   TELEGRAM_BOT_TOKEN="your_bot_token"
   DATABASE_URL="postgresql://postgres:password@host:5432/db"
   JWT_SECRET="your_jwt_secret"
   ORBIT_BOT_API_KEY="your_api_key"
   ```

4. **Deploy**
   ```bash
   railway up
   ```

### 3. Deploy Frontend to Vercel

1. **Create Vercel Account**
   - Go to [vercel.com](https://vercel.com)
   - Sign up with GitHub

2. **Deploy Dashboard**
   ```bash
   cd dashboard
   npm install
   npm run build
   
   # Install Vercel CLI
   npm install -g vercel
   
   # Deploy
   vercel --prod
   ```

3. **Update Vercel Config**
   - Edit `vercel.json` to point to your Railway URL
   - Redeploy with `vercel --prod`

### 4. Configure Telegram Bot

1. **Set Webhook**
   ```bash
   curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
        -d "url=https://your-railway-app.railway.app/api/v1/bot/webhook"
   ```

2. **Test Bot**
   - Send `/start` to your bot
   - Should respond with welcome message

## Alternative: Render Deployment

### 1. Deploy to Render

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create Web Service**
   - Connect your GitHub repo
   - Use `deploy/requirements-slim.txt`
   - Set build command: `pip install -r deploy/requirements-slim.txt`
   - Set start command: `uvicorn api.index:app --host 0.0.0.0 --port $PORT`

3. **Create PostgreSQL Database**
   - Add PostgreSQL service
   - Get connection string
   - Set as `DATABASE_URL` environment variable

## Environment Variables Required

```env
# Core
TELEGRAM_BOT_TOKEN="your_bot_token"
DATABASE_URL="postgresql://user:pass@host:5432/db"
JWT_SECRET="your_jwt_secret"

# Bot API
ORBIT_BOT_API_KEY="random_string"
INSTITUTION_SLUG="sit"

# Frontend
ORBIT_BACKEND_BASE_URL="https://your-backend-url.com"
```

## What You Get for Free

### Railway ($5/month credit)
- **Backend**: 500 hours/month
- **Database**: 1GB PostgreSQL
- **Bandwidth**: 100GB/month

### Vercel (Free)
- **Frontend**: Unlimited static sites
- **Bandwidth**: 100GB/month
- **Builds**: 100/month

### Render (Free)
- **Backend**: 750 hours/month
- **Database**: 256MB PostgreSQL
- **Bandwidth**: 100GB/month

## Simplified Architecture

```
Vercel (Frontend)  ->  Railway/Render (Backend API)  ->  PostgreSQL
                        |
                        v
                   Telegram Bot API
```

## Next Steps

1. **Choose Platform**: Railway (easier) or Render (more flexible)
2. **Deploy Backend**: Follow platform-specific steps
3. **Deploy Frontend**: Vercel or Render static
4. **Configure Bot**: Set webhook and test
5. **Monitor**: Check logs and health endpoint

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check DATABASE_URL format
   - Ensure PostgreSQL is running
   - Verify network access

2. **Bot Not Responding**
   - Check webhook URL
   - Verify bot token
   - Check Railway logs

3. **Frontend Can't Connect**
   - Update API base URL
   - Check CORS settings
   - Verify environment variables

### Health Check

Always test: `GET /api/v1/health`

Should return:
```json
{
  "status": "operational",
  "version": "1.0.0",
  "release": "orbit",
  "setup_required": false
}
```

## Production Tips

1. **Use Railway** for easiest deployment
2. **Monitor usage** to stay within free limits
3. **Set up alerts** for downtime
4. **Backup database** regularly
5. **Use environment variables** for all secrets

That's it! Your Academic Hub will be live for free.
