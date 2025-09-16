#!/usr/bin/env python3
import asyncio
import motor.motor_asyncio
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.frisorDB

BACKEND_URL = 'https://stylista-admin.preview.emergentagent.com'

def fix_url(url_string):
    """Fix URLs in strings to use the new API route"""
    if not url_string:
        return url_string
    
    # Replace old paths with new API paths
    url_string = url_string.replace('/uploads/images/', '/api/uploads/images/')
    url_string = url_string.replace('/uploads/avatars/', '/api/uploads/avatars/')
    url_string = url_string.replace('/uploads/videos/', '/api/uploads/videos/')
    
    return url_string

async def fix_gallery_urls():
    """Fix gallery image URLs to use the new API route"""
    print("Fixing gallery image URLs...")
    
    # Update gallery items
    gallery_items = await db.gallery.find({}).to_list(length=None)
    
    for item in gallery_items:
        updated = False
        original_before = item.get('before_image', '')
        original_after = item.get('after_image', '')
        
        # Fix before_image URL
        if item.get('before_image'):
            fixed_before = fix_url(item['before_image'])
            if fixed_before != original_before:
                item['before_image'] = fixed_before
                updated = True
            
        # Fix after_image URL
        if item.get('after_image'):
            fixed_after = fix_url(item['after_image'])
            if fixed_after != original_after:
                item['after_image'] = fixed_after
                updated = True
            
        if updated:
            await db.gallery.update_one(
                {"_id": item["_id"]}, 
                {"$set": {
                    "before_image": item.get('before_image'),
                    "after_image": item.get('after_image')
                }}
            )
            print(f"Updated gallery item: {item.get('title', 'Unknown')} - before: {original_before} -> {item.get('before_image')}, after: {original_after} -> {item.get('after_image')}")
    
    print("Gallery URLs fixed!")

async def fix_staff_urls():
    """Fix staff avatar URLs to use the new API route"""
    print("Fixing staff avatar URLs...")
    
    # Update staff avatars
    staff_members = await db.staff.find({}).to_list(length=None)
    
    for staff in staff_members:
        if staff.get('avatar_url'):
            original_url = staff['avatar_url']
            fixed_url = fix_url(staff['avatar_url'])
            if fixed_url != original_url:
                await db.staff.update_one(
                    {"_id": staff["_id"]}, 
                    {"$set": {"avatar_url": fixed_url}}
                )
                print(f"Updated staff avatar: {staff.get('name', 'Unknown')} - {original_url} -> {fixed_url}")
    
    print("Staff avatar URLs fixed!")

async def fix_page_urls():
    """Fix page featured image URLs and content images to use the new API route"""
    print("Fixing page URLs...")
    
    # Update page featured images and content
    pages = await db.pages.find({}).to_list(length=None)
    
    for page in pages:
        updated = False
        update_data = {}
        
        # Fix featured_image URL
        if page.get('featured_image'):
            original_featured = page['featured_image']
            fixed_featured = fix_url(page['featured_image'])
            if fixed_featured != original_featured:
                update_data['featured_image'] = fixed_featured
                updated = True
                print(f"Page {page.get('title', 'Unknown')}: featured_image {original_featured} -> {fixed_featured}")
        
        # Fix any images in the images array
        if page.get('images'):
            fixed_images = []
            images_updated = False
            for image_url in page['images']:
                fixed_image = fix_url(image_url)
                fixed_images.append(fixed_image)
                if fixed_image != image_url:
                    images_updated = True
                    print(f"Page {page.get('title', 'Unknown')}: image {image_url} -> {fixed_image}")
            if images_updated:
                update_data['images'] = fixed_images
                updated = True
        
        # Fix any videos in the videos array
        if page.get('videos'):
            fixed_videos = []
            videos_updated = False
            for video_url in page['videos']:
                fixed_video = fix_url(video_url)
                fixed_videos.append(fixed_video)
                if fixed_video != video_url:
                    videos_updated = True
                    print(f"Page {page.get('title', 'Unknown')}: video {video_url} -> {fixed_video}")
            if videos_updated:
                update_data['videos'] = fixed_videos
                updated = True
        
        # Fix URLs in content (for images embedded in rich text)
        if page.get('content'):
            original_content = page['content'] 
            fixed_content = fix_url(original_content)
            if fixed_content != original_content:
                update_data['content'] = fixed_content
                updated = True
                print(f"Page {page.get('title', 'Unknown')}: content URLs updated")
                
        if updated:
            await db.pages.update_one(
                {"_id": page["_id"]}, 
                {"$set": update_data}
            )
    
    print("Page URLs fixed!")

async def fix_site_settings():
    """Fix any image URLs in site settings"""
    print("Fixing site settings URLs...")
    
    settings = await db.site_settings.find({}).to_list(length=None)
    
    for setting in settings:
        updated = False
        update_data = {}
        
        # Check all fields for potential image URLs
        for field, value in setting.items():
            if field != '_id' and isinstance(value, str) and '/uploads/' in value:
                fixed_value = fix_url(value)
                if fixed_value != value:
                    update_data[field] = fixed_value
                    updated = True
                    print(f"Site setting {field}: {value} -> {fixed_value}")
                    
        if updated:
            await db.site_settings.update_one(
                {"_id": setting["_id"]},
                {"$set": update_data}
            )
    
    print("Site settings URLs fixed!")

async def main():
    print("Starting comprehensive URL fixes...")
    await fix_gallery_urls()
    await fix_staff_urls()
    await fix_page_urls()
    await fix_site_settings()
    print("All URLs fixed!")
    
if __name__ == "__main__":
    asyncio.run(main())