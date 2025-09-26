# 🗄️ MySQL Database Setup Guide

## 📁 **SQL FILE TO IMPORT**

**File:** `backend/mysql_schema.sql`
**Location:** In your downloaded ZIP: `frisor-lafata-COMPLETE-website.zip/backend/mysql_schema.sql`

## 🔧 **Step 1: Create MySQL Database**

### **In cPanel:**
1. **Go to cPanel → MySQL Databases**
2. **Create New Database:**
   - Database Name: `frisor_lafata` (or any name you prefer)
   - Click "Create Database"

3. **Create Database User:**
   - Username: `frisor_user` (or any name)
   - Password: (create a secure password)
   - Click "Create User"

4. **Add User to Database:**
   - Select the user and database
   - Grant "ALL PRIVILEGES"
   - Click "Make Changes"

## 📤 **Step 2: Import SQL Schema**

### **Option A: cPanel phpMyAdmin**
1. **Go to cPanel → phpMyAdmin**
2. **Select your database** (`frisor_lafata`)
3. **Click "Import" tab**
4. **Choose File:** Upload `mysql_schema.sql`
5. **Click "Go"**

### **Option B: Upload via cPanel File Manager**
1. **Upload `mysql_schema.sql` to your account**
2. **Go to cPanel → MySQL Databases**
3. **Click "Run SQL Query"**
4. **Copy and paste the content** of `mysql_schema.sql`
5. **Click "Go"**

## ⚙️ **Step 3: Configure Backend Connection**

### **File to Edit:** `backend/.env`

```bash
# Database Configuration
DB_TYPE="mysql"
MYSQL_HOST="localhost"
MYSQL_PORT="3306"
MYSQL_USER="your_username_here"     # ← Your MySQL username
MYSQL_PASSWORD="your_password_here" # ← Your MySQL password  
MYSQL_DATABASE="frisor_lafata"      # ← Your database name

# Legacy MongoDB (can be ignored now)
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"

# Application Configuration
CORS_ORIGINS="*"
SECRET_KEY="frisor-lafata-secret-key-2024-very-secure"

# Email Configuration (for booking confirmations)
EMAIL_USER="your-email@gmail.com"    # ← Your email
EMAIL_PASSWORD="your-app-password"   # ← Your email app password

# PayPal Configuration (for payments)
PAYPAL_CLIENT_ID="your_paypal_client_id"
PAYPAL_CLIENT_SECRET="your_paypal_secret"
PAYPAL_SANDBOX_MODE="true"  # Set to "false" for live payments
```

## 📊 **What the Database Contains**

The SQL file creates:

### **Tables:**
- `users` - User accounts and admin access
- `services` - Barbershop services with prices
- `staff` - Staff members with schedules
- `bookings` - Customer appointments
- `gallery` - Before/after photos
- `pages` - CMS pages (about, contact, etc.)
- `site_settings` - Website configuration
- `staff_breaks` - Staff vacation/break schedules
- `homepage_sections` - Customizable homepage layout

### **Default Data:**
- ✅ Site settings with your barbershop info
- ✅ Default homepage sections
- ✅ Basic structure ready for your content

## 🔐 **Step 4: Security Notes**

### **Database User Permissions:**
- Only grant access to YOUR database
- Use a strong password
- Don't use "root" user for the application

### **Environment Variables:**
- Keep `.env` file secure
- Never share database credentials
- Use app-specific passwords for email

## 🚀 **Step 5: Test Database Connection**

After setting up:

1. **Upload backend files** to your hosting
2. **Configure `.env` with your database details**
3. **Test the connection** via admin panel
4. **Import any existing data** if needed

## 📋 **Complete Configuration Example**

```bash
# Your actual configuration might look like:
DB_TYPE="mysql"
MYSQL_HOST="localhost"
MYSQL_USER="frisor_db_user"
MYSQL_PASSWORD="SecurePass123!"
MYSQL_DATABASE="frisor_lafata"

# Your email for booking confirmations
EMAIL_USER="info@frisorlafata.dk"
EMAIL_PASSWORD="your-gmail-app-password"

# Your PayPal for payments (optional)
PAYPAL_CLIENT_ID="your-actual-paypal-client-id"
PAYPAL_SANDBOX_MODE="false"  # For live payments
```

## ✅ **Verification Checklist**

- [ ] MySQL database created in cPanel
- [ ] Database user created with full privileges
- [ ] SQL schema imported successfully
- [ ] `.env` file configured with correct credentials
- [ ] Backend uploaded to hosting
- [ ] Email settings configured
- [ ] PayPal settings configured (if using payments)

## 🆘 **Common Issues**

### **Import Fails:**
- Check file size limits in phpMyAdmin
- Try importing in smaller chunks
- Verify MySQL version compatibility

### **Connection Fails:**
- Double-check username/password
- Ensure database user has privileges
- Verify hostname (usually "localhost")

### **Tables Not Created:**
- Check for SQL syntax errors
- Verify user has CREATE permissions
- Look at phpMyAdmin error logs

Your database will be completely independent and won't disappear when the Emergent session ends! 🎉