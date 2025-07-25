# 🚀 Vercel Deployment Guide

आपका Free Fire Token Generator अब Vercel के लिए fully optimized है।

## Deploy करने के Steps:

### 1. Vercel Account Setup
```bash
# Vercel CLI install करें
npm i -g vercel

# Login करें
vercel login
```

### 2. Environment Variables Set करें
Vercel dashboard में जाकर ये environment variables add करें:

```bash
DATABASE_URL=postgresql://neondb_owner:npg_2wvRQWkasIr9@ep-old-king-a1qaotvu-pooler.ap-southeast-1.aws.neon.tech/neondb
VERCEL=1
```

### 3. Deploy करें
```bash
# Project root directory में जाकर
vercel --prod
```

## 🎯 API Endpoints (Deploy के बाद):

Your API URL: `https://your-project-name.vercel.app`

- **GET /** - Service status check
- **GET /like?uid=2942087766** - Send likes (auto-detect server)  
- **GET /like?uid=3978250517&server_name=IND** - Send likes to specific server
- **GET /tokens** - View generated tokens from database
- **GET /records** - View player records

## ✅ Vercel Optimizations:

1. **Serverless Ready**: Token generation disabled on Vercel (uses database tokens)
2. **Fast Response**: Database-only approach for instant token loading
3. **60s Timeout**: Maximum function duration optimized
4. **Auto Scaling**: Handles multiple requests automatically

## 🧪 Test Commands:

```bash
# Test deployed API
curl "https://your-project.vercel.app/"
curl "https://your-project.vercel.app/like?uid=2942087766"
curl "https://your-project.vercel.app/tokens"
```

## 📊 Expected Response:
```json
{
  "status": 3,
  "message": "⏳ 99 like requests sent successfully",
  "server_detected": "PK", 
  "requests_sent": 99,
  "player": {
    "uid": 2942087766,
    "nickname": "리틀뿅5803S"
  }
}
```

आपका API अब production-ready है और Vercel पर deploy के लिए तैयार है! 🎉