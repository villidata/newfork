#!/usr/bin/env python3
"""
Migration script to convert data from MongoDB to MySQL
"""
import asyncio
import motor.motor_asyncio
import os
import json
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
from database import init_db, close_db, get_db_connection, insert_record

# Load environment variables
load_dotenv()

# MongoDB connection (for reading old data)
MONGO_URL = os.environ.get('MONGO_URL')
mongo_client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
mongo_db = mongo_client.frisorDB

async def migrate_users():
    """Migrate users from MongoDB to MySQL"""
    print("Migrating users...")
    
    users = await mongo_db.users.find({}).to_list(length=None)
    user_passwords = await mongo_db.user_passwords.find({}).to_list(length=None)
    
    # Create password lookup
    password_lookup = {pwd['user_id']: pwd['password'] for pwd in user_passwords}
    
    for user in users:
        user_data = {
            'id': user.get('id', str(uuid.uuid4())),
            'name': user.get('name', ''),
            'email': user.get('email', ''),
            'phone': user.get('phone', ''),
            'is_admin': user.get('is_admin', False),
            'created_at': user.get('created_at', datetime.now(timezone.utc))
        }
        
        try:
            await insert_record('users', user_data)
            
            # Insert password if exists
            if user_data['id'] in password_lookup:
                password_data = {
                    'user_id': user_data['id'],
                    'password': password_lookup[user_data['id']]
                }
                await insert_record('user_passwords', password_data)
                
            print(f"Migrated user: {user_data['name']} ({user_data['email']})")
        except Exception as e:
            print(f"Error migrating user {user_data.get('email', 'unknown')}: {e}")

async def migrate_services():
    """Migrate services from MongoDB to MySQL"""
    print("Migrating services...")
    
    services = await mongo_db.services.find({}).to_list(length=None)
    
    for service in services:
        service_data = {
            'id': service.get('id', str(uuid.uuid4())),
            'name': service.get('name', ''),
            'duration_minutes': service.get('duration_minutes', 30),
            'price': float(service.get('price', 0)),
            'description': service.get('description', ''),
            'category': service.get('category', 'general'),
            'icon': service.get('icon', '✨'),
            'created_at': service.get('created_at', datetime.now(timezone.utc))
        }
        
        try:
            await insert_record('services', service_data)
            print(f"Migrated service: {service_data['name']}")
        except Exception as e:
            print(f"Error migrating service {service_data.get('name', 'unknown')}: {e}")

async def migrate_staff():
    """Migrate staff from MongoDB to MySQL"""
    print("Migrating staff...")
    
    staff_members = await mongo_db.staff.find({}).to_list(length=None)
    
    for staff in staff_members:
        staff_data = {
            'id': staff.get('id', str(uuid.uuid4())),
            'name': staff.get('name', ''),
            'bio': staff.get('bio', ''),
            'experience_years': staff.get('experience_years', 0),
            'specialties': staff.get('specialties', []),
            'phone': staff.get('phone', ''),
            'email': staff.get('email', ''),
            'avatar_url': staff.get('avatar_url', ''),
            'portfolio_images': staff.get('portfolio_images', []),
            'available_hours': staff.get('available_hours', {}),
            'created_at': staff.get('created_at', datetime.now(timezone.utc))
        }
        
        try:
            await insert_record('staff', staff_data)
            print(f"Migrated staff: {staff_data['name']}")
        except Exception as e:
            print(f"Error migrating staff {staff_data.get('name', 'unknown')}: {e}")

async def migrate_bookings():
    """Migrate bookings from MongoDB to MySQL"""
    print("Migrating bookings...")
    
    bookings = await mongo_db.bookings.find({}).to_list(length=None)
    
    for booking in bookings:
        booking_data = {
            'id': booking.get('id', str(uuid.uuid4())),
            'customer_id': booking.get('customer_id', str(uuid.uuid4())),
            'customer_name': booking.get('customer_name', ''),
            'customer_email': booking.get('customer_email', ''),
            'customer_phone': booking.get('customer_phone', ''),
            'staff_id': booking.get('staff_id', ''),
            'services': booking.get('services', []),
            'booking_date': booking.get('date', datetime.now().date()),
            'booking_time': booking.get('time', datetime.now().time()),
            'total_duration': booking.get('total_duration', 30),
            'total_price': float(booking.get('total_price', 0)),
            'payment_method': booking.get('payment_method', 'cash'),
            'payment_status': booking.get('payment_status', 'pending'),
            'status': booking.get('status', 'pending'),
            'notes': booking.get('notes', ''),
            'admin_notes': booking.get('admin_notes', ''),
            'created_at': booking.get('created_at', datetime.now(timezone.utc))
        }
        
        try:
            await insert_record('bookings', booking_data)
            print(f"Migrated booking: {booking_data['id']}")
        except Exception as e:
            print(f"Error migrating booking {booking_data.get('id', 'unknown')}: {e}")

async def migrate_gallery():
    """Migrate gallery from MongoDB to MySQL"""
    print("Migrating gallery...")
    
    gallery_items = await mongo_db.gallery.find({}).to_list(length=None)
    
    for item in gallery_items:
        gallery_data = {
            'id': item.get('id', str(uuid.uuid4())),
            'title': item.get('title', ''),
            'description': item.get('description', ''),
            'before_image': item.get('before_image', ''),
            'after_image': item.get('after_image', ''),
            'service_type': item.get('service_type', ''),
            'staff_id': item.get('staff_id'),
            'is_featured': item.get('is_featured', False),
            'created_at': item.get('created_at', datetime.now(timezone.utc))
        }
        
        try:
            await insert_record('gallery', gallery_data)
            print(f"Migrated gallery item: {gallery_data['title']}")
        except Exception as e:
            print(f"Error migrating gallery item {gallery_data.get('title', 'unknown')}: {e}")

async def migrate_pages():
    """Migrate pages from MongoDB to MySQL"""
    print("Migrating pages...")
    
    pages = await mongo_db.pages.find({}).to_list(length=None)
    
    for page in pages:
        page_data = {
            'id': page.get('id', str(uuid.uuid4())),
            'title': page.get('title', ''),
            'slug': page.get('slug', ''),
            'content': page.get('content', ''),
            'excerpt': page.get('excerpt', ''),
            'meta_description': page.get('meta_description', ''),
            'page_type': page.get('page_type', 'page'),
            'categories': page.get('categories', []),
            'tags': page.get('tags', []),
            'featured_image': page.get('featured_image', ''),
            'images': page.get('images', []),
            'videos': page.get('videos', []),
            'is_published': page.get('is_published', True),
            'show_in_navigation': page.get('show_in_navigation', False),
            'navigation_order': page.get('navigation_order', 0),
            'created_at': page.get('created_at', datetime.now(timezone.utc))
        }
        
        try:
            await insert_record('pages', page_data)
            print(f"Migrated page: {page_data['title']}")
        except Exception as e:
            print(f"Error migrating page {page_data.get('title', 'unknown')}: {e}")

async def migrate_settings():
    """Migrate site settings from MongoDB to MySQL"""
    print("Migrating site settings...")
    
    settings = await mongo_db.site_settings.find_one({})
    
    if settings:
        settings_data = {
            'id': 1,  # Fixed ID for settings
            'site_title': settings.get('site_title', 'Frisor LaFata'),
            'site_description': settings.get('site_description', 'Klassisk barbering siden 2010'),
            'contact_phone': settings.get('contact_phone', '+45 12 34 56 78'),
            'contact_email': settings.get('contact_email', 'info@frisorlafata.dk'),
            'address': settings.get('address', 'Hovedgaden 123, 1000 København'),
            'hero_title': settings.get('hero_title', 'Klassisk Barbering'),
            'hero_subtitle': settings.get('hero_subtitle', 'i Hjertet af Byen'),
            'hero_description': settings.get('hero_description', 'Oplev den autentiske barber-oplevelse hos Frisor LaFata.'),
            'hero_image': settings.get('hero_image', ''),
            # PayPal settings
            'paypal_client_id': settings.get('paypal_client_id', ''),
            'paypal_client_secret': settings.get('paypal_client_secret', ''),
            'paypal_sandbox_mode': settings.get('paypal_sandbox_mode', True),
            # Email settings
            'email_smtp_server': settings.get('email_smtp_server', 'smtp.gmail.com'),
            'email_smtp_port': settings.get('email_smtp_port', 587),
            'email_user': settings.get('email_user', ''),
            'email_password': settings.get('email_password', ''),
            # Email templates
            'email_subject_template': settings.get('email_subject_template', ''),
            'email_body_template': settings.get('email_body_template', ''),
            'reminder_subject_template': settings.get('reminder_subject_template', ''),
            'reminder_body_template': settings.get('reminder_body_template', ''),
            'email_confirmation_subject': settings.get('email_confirmation_subject', ''),
            'email_confirmation_body': settings.get('email_confirmation_body', ''),
            'email_change_subject': settings.get('email_change_subject', ''),
            'email_change_body': settings.get('email_change_body', ''),
            # Social Media Settings
            'social_media_enabled': settings.get('social_media_enabled', True),
            'social_media_title': settings.get('social_media_title', 'Follow Us'),
            'social_media_description': settings.get('social_media_description', 'Se vores seneste arbejde og tilbud på sociale medier'),
            # Instagram
            'instagram_enabled': settings.get('instagram_enabled', True),
            'instagram_username': settings.get('instagram_username', ''),
            'instagram_hashtag': settings.get('instagram_hashtag', ''),
            'instagram_embed_code': settings.get('instagram_embed_code', ''),
            # Facebook
            'facebook_enabled': settings.get('facebook_enabled', True),
            'facebook_page_url': settings.get('facebook_page_url', ''),
            'facebook_embed_code': settings.get('facebook_embed_code', ''),
            # TikTok
            'tiktok_enabled': settings.get('tiktok_enabled', False),
            'tiktok_username': settings.get('tiktok_username', ''),
            'tiktok_embed_code': settings.get('tiktok_embed_code', ''),
            # Twitter/X
            'twitter_enabled': settings.get('twitter_enabled', False),
            'twitter_username': settings.get('twitter_username', ''),
            'twitter_embed_code': settings.get('twitter_embed_code', ''),
            # YouTube
            'youtube_enabled': settings.get('youtube_enabled', False),
            'youtube_channel_url': settings.get('youtube_channel_url', ''),
            'youtube_embed_code': settings.get('youtube_embed_code', '')
        }
        
        try:
            # Use INSERT ... ON DUPLICATE KEY UPDATE for settings
            async with get_db_connection() as (connection, cursor):
                columns = list(settings_data.keys())
                placeholders = ['%s'] * len(columns)
                values = list(settings_data.values())
                
                # Create the update clause for ON DUPLICATE KEY UPDATE
                update_clause = ', '.join([f"{col} = VALUES({col})" for col in columns if col != 'id'])
                
                query = f"""
                INSERT INTO site_settings ({', '.join(columns)}) 
                VALUES ({', '.join(placeholders)}) 
                ON DUPLICATE KEY UPDATE {update_clause}
                """
                
                await cursor.execute(query, values)
                print("Migrated site settings")
        except Exception as e:
            print(f"Error migrating settings: {e}")

async def migrate_staff_breaks():
    """Migrate staff breaks from MongoDB to MySQL"""
    print("Migrating staff breaks...")
    
    breaks = await mongo_db.staff_breaks.find({}).to_list(length=None)
    
    for break_item in breaks:
        break_data = {
            'id': break_item.get('id', str(uuid.uuid4())),
            'staff_id': break_item.get('staff_id', ''),
            'start_date': break_item.get('start_date', datetime.now().date()),
            'end_date': break_item.get('end_date', datetime.now().date()),
            'start_time': break_item.get('start_time'),
            'end_time': break_item.get('end_time'),
            'reason': break_item.get('reason', ''),
            'is_recurring': break_item.get('is_recurring', False),
            'recurrence_pattern': break_item.get('recurrence_pattern', ''),
            'created_at': break_item.get('created_at', datetime.now(timezone.utc))
        }
        
        try:
            await insert_record('staff_breaks', break_data)
            print(f"Migrated staff break: {break_data['id']}")
        except Exception as e:
            print(f"Error migrating staff break {break_data.get('id', 'unknown')}: {e}")

async def main():
    """Main migration function"""
    print("Starting MongoDB to MySQL migration...")
    
    try:
        # Initialize MySQL database
        await init_db()
        
        # Run migrations in order (users first, then references)
        await migrate_users()
        await migrate_services()  
        await migrate_staff()
        await migrate_bookings()
        await migrate_gallery()
        await migrate_pages()
        await migrate_settings()
        await migrate_staff_breaks()
        
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close connections
        await close_db()
        mongo_client.close()

if __name__ == "__main__":
    asyncio.run(main())