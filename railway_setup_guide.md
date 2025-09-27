# 🚂 Railway.app Backend Setup Guide

## Why Railway for Shared cPanel Hosting?

- ✅ **Free tier available**
- ✅ **FastAPI support** 
- ✅ **Easy deployment**
- ✅ **Automatic HTTPS**
- ✅ **No server management**

## Step-by-Step Setup

### Step 1: Create Railway Account
1. Go to **railway.app**
2. **Sign up** with GitHub account
3. **Verify email**

### Step 2: Prepare Backend Code
1. **Download**: `BACKEND-SETUP-PACKAGE.zip`
2. **Extract** to a folder on your computer
3. **Create GitHub repository** (public or private)
4. **Upload backend files** to GitHub

### Step 3: Deploy to Railway
1. **Railway Dashboard** → "New Project"
2. **Deploy from GitHub repo**
3. **Select your backend repository**
4. **Railway auto-detects** Python/FastAPI

### Step 4: Configure Environment Variables
In Railway dashboard, add:
```
DB_TYPE=mysql
MYSQL_HOST=your_mysql_host
MYSQL_USER=target_lafata
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=target_lafata
CORS_ORIGINS=https://frisorlafata.dk
```

### Step 5: Database Options

#### Option A: Railway PostgreSQL (Easiest)
- Railway provides free PostgreSQL
- Need to convert MySQL schema to PostgreSQL

#### Option B: External MySQL
- Use PlanetScale (free MySQL)
- Or connect to your cPanel MySQL (if external access allowed)

#### Option C: Railway MySQL
- Available in paid tier

### Step 6: Get Railway URL
- After deployment: `https://your-app-name.railway.app`
- Test: `https://your-app-name.railway.app/api/settings`

### Step 7: Update Frontend
Create new frontend build pointing to Railway:
```bash
REACT_APP_BACKEND_URL=https://your-app-name.railway.app
```

## Free Tier Limits
- **500 hours/month** (about 16 hours/day)
- **1GB RAM**
- **1GB disk space**
- **Perfect for small websites**