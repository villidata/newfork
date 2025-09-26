-- Frisor LaFata MySQL Database Schema
-- Updated for target_lafata database with MySQL compatibility fixes

CREATE DATABASE IF NOT EXISTS target_lafata CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE target_lafata;

-- Users table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Staff table
CREATE TABLE staff (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    experience_years INT NOT NULL,
    bio TEXT,
    avatar_url TEXT,
    instagram_url VARCHAR(255),
    facebook_url VARCHAR(255),
    linkedin_url VARCHAR(255),
    twitter_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Services table (FIXED - removed emoji default)
CREATE TABLE services (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    duration_minutes INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    description TEXT,
    category VARCHAR(100) DEFAULT 'general',
    icon VARCHAR(100) DEFAULT 'sparkles',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Bookings table
CREATE TABLE bookings (
    id VARCHAR(36) PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    customer_phone VARCHAR(50),
    date DATE NOT NULL,
    time TIME NOT NULL,
    staff_id VARCHAR(36),
    service_ids JSON,
    total_duration INT NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    notes TEXT,
    booking_type VARCHAR(50) DEFAULT 'individual',
    is_home_service BOOLEAN DEFAULT FALSE,
    home_service_address TEXT,
    payment_method VARCHAR(50) DEFAULT 'cash',
    payment_status VARCHAR(50) DEFAULT 'pending',
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE SET NULL
);

-- Gallery table
CREATE TABLE gallery (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255),
    description TEXT,
    before_image TEXT NOT NULL,
    after_image TEXT NOT NULL,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Pages table
CREATE TABLE pages (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    content TEXT,
    meta_description TEXT,
    is_published BOOLEAN DEFAULT TRUE,
    page_type VARCHAR(50) DEFAULT 'page',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Site settings table (UPDATED with video background fields)
CREATE TABLE site_settings (
    id VARCHAR(36) PRIMARY KEY,
    site_title VARCHAR(255) DEFAULT 'Frisor LaFata',
    site_description TEXT DEFAULT 'Klassisk barbering siden 2010',
    contact_phone VARCHAR(50) DEFAULT '+45 12 34 56 78',
    contact_email VARCHAR(255) DEFAULT 'info@frisorlafata.dk',
    address TEXT DEFAULT 'Hovedgaden 123, 1000 København',
    hero_title VARCHAR(255) DEFAULT 'Klassisk Barbering',
    hero_subtitle VARCHAR(255) DEFAULT 'i Hjertet af Byen',
    hero_description TEXT DEFAULT 'Oplev den autentiske barber-oplevelse hos Frisor LaFata.',
    hero_image TEXT,
    hero_video TEXT,
    hero_video_enabled BOOLEAN DEFAULT FALSE,
    hero_text_overlay_enabled BOOLEAN DEFAULT TRUE,
    hero_image_opacity DECIMAL(3,2) DEFAULT 0.70,
    booking_system_enabled BOOLEAN DEFAULT TRUE,
    paypal_client_id VARCHAR(255),
    paypal_client_secret VARCHAR(255),
    paypal_sandbox_mode BOOLEAN DEFAULT TRUE,
    email_enabled BOOLEAN DEFAULT FALSE,
    email_smtp_server VARCHAR(255) DEFAULT 'smtp.gmail.com',
    email_smtp_port INT DEFAULT 587,
    email_username VARCHAR(255),
    email_password VARCHAR(255),
    email_use_tls BOOLEAN DEFAULT TRUE,
    social_media_enabled BOOLEAN DEFAULT FALSE,
    social_media_facebook_url TEXT,
    social_media_instagram_url TEXT,
    social_media_twitter_url TEXT,
    social_media_linkedin_url TEXT,
    social_media_youtube_url TEXT,
    social_media_title VARCHAR(255) DEFAULT 'Follow Us',
    social_media_description TEXT DEFAULT 'Se vores seneste arbejde og tilbud på sociale medier',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Corporate bookings table
CREATE TABLE corporate_bookings (
    id VARCHAR(36) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(50),
    company_address TEXT,
    date DATE NOT NULL,
    time TIME NOT NULL,
    employees JSON NOT NULL,
    travel_fee DECIMAL(10,2) DEFAULT 0.00,
    total_price DECIMAL(10,2) NOT NULL,
    notes TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(50) DEFAULT 'invoice',
    payment_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Staff breaks table
CREATE TABLE staff_breaks (
    id VARCHAR(36) PRIMARY KEY,
    staff_id VARCHAR(36) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    break_type VARCHAR(50) NOT NULL,
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (staff_id) REFERENCES staff(id) ON DELETE CASCADE
);

-- Homepage sections table
CREATE TABLE homepage_sections (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    section_type VARCHAR(100) NOT NULL,
    content JSON,
    display_order INT NOT NULL,
    is_visible BOOLEAN DEFAULT TRUE,
    background_color VARCHAR(7) DEFAULT '#000000',
    text_color VARCHAR(7) DEFAULT '#D4AF37',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_bookings_date_time ON bookings(date, time);
CREATE INDEX idx_bookings_staff_id ON bookings(staff_id);
CREATE INDEX idx_corporate_bookings_date ON corporate_bookings(date);
CREATE INDEX idx_staff_breaks_staff_id ON staff_breaks(staff_id);
CREATE INDEX idx_staff_breaks_dates ON staff_breaks(start_date, end_date);

-- Insert default site settings
INSERT INTO site_settings (id, site_title, hero_title, hero_subtitle, hero_description) 
VALUES (
    UUID(), 
    'Frisør LaFata',
    'Frisør LaFata', 
    'Klassik Barbering',
    'Oplev den autentiske barber-oplevelse hos Frisør LaFata. Vi kombinerer traditionel håndværk med moderne teknikker.'
) ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;