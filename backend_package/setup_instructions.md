# 🚀 FastAPI Backend Setup for cPanel

## Prerequisites Check

1. **Upload `hosting_check.php` to your cPanel and visit it**
2. **Check if your hosting supports:**
   - Python 3.7+ 
   - pip package manager
   - MySQL databases
   - Python Apps in cPanel

## Setup Steps

### Step 1: Database Setup
1. **Create MySQL database:** `target_lafata`
2. **Create MySQL user:** `target_lafata` 
3. **Import schema:** Upload and import `mysql_schema.sql`

### Step 2: Backend Files Upload
1. **Create folder:** `api` in your cPanel root (not public_html)
2. **Upload all backend files** to the `api` folder:
   ```
   /home/yourusername/api/
   ├── server.py
   ├── app.py
   ├── database.py
   ├── requirements.txt
   ├── .env
   └── uploads/
   ```

### Step 3: Environment Configuration
1. **Copy `.env.template` to `.env`**
2. **Update with your settings:**
   ```bash
   MYSQL_USER="target_lafata"
   MYSQL_PASSWORD="your_actual_password"
   MYSQL_DATABASE="target_lafata"
   CORS_ORIGINS="https://frisorlafata.dk"
   ```

### Step 4: Python App Setup (cPanel)
1. **Go to cPanel → Python Apps**
2. **Create New App:**
   - Python Version: 3.8+
   - App Root: `/home/yourusername/api`
   - App URL: `/api` 
   - Startup File: `app.py`
   - Application Object: `application`

### Step 5: Install Dependencies
1. **In cPanel Python App terminal:**
   ```bash
   pip install -r requirements.txt
   ```

### Step 6: Test Backend
1. **Visit:** `https://frisorlafata.dk/api/settings`
2. **Should return:** JSON data, not HTML

### Step 7: Update Frontend
1. **Use:** `FRONTEND-YOUR-DOMAIN.zip` (points to your domain)
2. **Upload to:** `public_html/`

## Alternative Hosting Options

If your cPanel doesn't support Python:

### Option A: Upgrade Hosting
- Look for hosting that supports Python/FastAPI
- Many providers offer Python support

### Option B: External Backend Service
- Railway.app (free tier)
- Render.com (free tier) 
- PythonAnywhere (free tier)
- Heroku (paid)

### Option C: VPS/Cloud
- DigitalOcean Droplet
- AWS EC2
- Google Cloud VM

## Troubleshooting

### Backend Not Starting
- Check Python version (3.7+)
- Verify all dependencies installed
- Check database connection settings

### API Returns HTML Instead of JSON  
- Verify Python app is running
- Check app URL mapping (/api)
- Ensure CORS settings correct

### Database Connection Failed
- Verify MySQL credentials
- Check database name matches
- Ensure user has proper permissions

## Testing Commands

```bash
# Test database connection
python -c "from database import get_db_connection; print('DB OK')"

# Test API endpoints
curl https://frisorlafata.dk/api/settings
curl https://frisorlafata.dk/api/staff
```