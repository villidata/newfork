-- Frisor LaFata MySQL Database Schema
-- Created for conversion from MongoDB

CREATE DATABASE IF NOT EXISTS frisor_lafata CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE frisor_lafata;

-- Users table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- User passwords (separate table for security)
CREATE TABLE user_passwords (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Services table
CREATE TABLE services (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    duration_minutes INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description TEXT,
    category VARCHAR(100) DEFAULT 'general',
    icon VARCHAR(100) DEFAULT '✨',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Staff table
CREATE TABLE staff (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    bio TEXT,
    experience_years INT DEFAULT 0,
    specialties JSON, -- Array of specialties
    phone VARCHAR(50),
    email VARCHAR(255),
    avatar_url TEXT,
    portfolio_images JSON, -- Array of image URLs
    available_hours JSON, -- Complex nested schedule data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Bookings table
CREATE TABLE bookings (
    id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(36) NOT NULL,
    customer_name VARCHAR(255),
    customer_email VARCHAR(255),
    customer_phone VARCHAR(50),
    staff_id VARCHAR(36) NOT NULL,
    services JSON, -- Array of service IDs
    booking_date DATE NOT NULL,
    booking_time TIME NOT NULL,
    total_duration INT NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) DEFAULT 'cash',
    payment_status VARCHAR(50) DEFAULT 'pending',
    status VARCHAR(50) DEFAULT 'pending',
    notes TEXT,
    admin_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
);

-- Gallery table
CREATE TABLE gallery (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    before_image TEXT NOT NULL,
    after_image TEXT NOT NULL,
    service_type VARCHAR(100),
    staff_id VARCHAR(36),
    is_featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE SET NULL
);

-- Pages table (for CMS functionality)
CREATE TABLE pages (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    content LONGTEXT,
    excerpt TEXT,
    meta_description TEXT,
    page_type VARCHAR(50) DEFAULT 'page',
    categories JSON, -- Array of categories
    tags JSON, -- Array of tags
    featured_image TEXT,
    images JSON, -- Array of image URLs
    videos JSON, -- Array of video URLs
    is_published BOOLEAN DEFAULT TRUE,
    show_in_navigation BOOLEAN DEFAULT FALSE,
    navigation_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Site settings table (single row table for site configuration)
CREATE TABLE site_settings (
    id INT PRIMARY KEY DEFAULT 1,
    site_title VARCHAR(255) DEFAULT 'Frisor LaFata',
    site_description TEXT DEFAULT 'Klassisk barbering siden 2010',
    contact_phone VARCHAR(50) DEFAULT '+45 12 34 56 78',
    contact_email VARCHAR(255) DEFAULT 'info@frisorlafata.dk',
    address TEXT DEFAULT 'Hovedgaden 123, 1000 København',
    hero_title VARCHAR(255) DEFAULT 'Klassisk Barbering',
    hero_subtitle VARCHAR(255) DEFAULT 'i Hjertet af Byen',
    hero_description TEXT DEFAULT 'Oplev den autentiske barber-oplevelse hos Frisor LaFata.',
    hero_image TEXT,
    -- PayPal settings
    paypal_client_id VARCHAR(255),
    paypal_client_secret VARCHAR(255),
    paypal_sandbox_mode BOOLEAN DEFAULT TRUE,
    -- Email settings
    email_smtp_server VARCHAR(255) DEFAULT 'smtp.gmail.com',
    email_smtp_port INT DEFAULT 587,
    email_user VARCHAR(255),
    email_password VARCHAR(255),
    -- Email templates
    email_subject_template TEXT,
    email_body_template TEXT,
    reminder_subject_template TEXT,
    reminder_body_template TEXT,
    email_confirmation_subject TEXT,
    email_confirmation_body TEXT,
    email_change_subject TEXT,
    email_change_body TEXT,
    -- Social Media Settings
    social_media_enabled BOOLEAN DEFAULT TRUE,
    social_media_title VARCHAR(255) DEFAULT 'Follow Us',
    social_media_description TEXT DEFAULT 'Se vores seneste arbejde og tilbud på sociale medier',
    -- Instagram
    instagram_enabled BOOLEAN DEFAULT TRUE,
    instagram_username VARCHAR(255),
    instagram_hashtag VARCHAR(255),
    instagram_embed_code TEXT,
    -- Facebook
    facebook_enabled BOOLEAN DEFAULT TRUE,
    facebook_page_url TEXT,
    facebook_embed_code TEXT,
    -- TikTok
    tiktok_enabled BOOLEAN DEFAULT FALSE,
    tiktok_username VARCHAR(255),
    tiktok_embed_code TEXT,
    -- Twitter/X
    twitter_enabled BOOLEAN DEFAULT FALSE,
    twitter_username VARCHAR(255),
    twitter_embed_code TEXT,
    -- YouTube
    youtube_enabled BOOLEAN DEFAULT FALSE,
    youtube_channel_url TEXT,
    youtube_embed_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CHECK (id = 1) -- Ensure only one settings record
);

-- Staff breaks table
CREATE TABLE staff_breaks (
    id VARCHAR(36) PRIMARY KEY,
    staff_id VARCHAR(36) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    reason VARCHAR(255),
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern VARCHAR(100), -- weekly, monthly, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
);

-- Insert default settings
INSERT INTO site_settings (id) VALUES (1) ON DUPLICATE KEY UPDATE id=id;

-- Create indexes for better performance
CREATE INDEX idx_bookings_date ON bookings(booking_date);
CREATE INDEX idx_bookings_staff ON bookings(staff_id);
CREATE INDEX idx_bookings_customer ON bookings(customer_id);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_gallery_featured ON gallery(is_featured);
CREATE INDEX idx_pages_published ON pages(is_published);
CREATE INDEX idx_pages_slug ON pages(slug);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_staff_breaks_dates ON staff_breaks(start_date, end_date);