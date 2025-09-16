#!/usr/bin/env python3
import asyncio
import motor.motor_asyncio
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL')
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.frisorDB

BACKEND_URL = 'https://stylista-admin.preview.emergentagent.com'

async def fix_gallery_urls():
    """Fix gallery image URLs to use the new API route"""
    print("Fixing gallery image URLs...")
    
    # Update gallery items
    gallery_items = await db.gallery.find({}).to_list(length=None)
    
    for item in gallery_items:
        updated = False
        
        # Fix before_image URL
        if item.get('before_image') and '/uploads/images/' in item['before_image']:
            item['before_image'] = item['before_image'].replace('/uploads/images/', '/api/uploads/images/')
            updated = True
            
        # Fix after_image URL
        if item.get('after_image') and '/uploads/images/' in item['after_image']:
            item['after_image'] = item['after_image'].replace('/uploads/images/', '/api/uploads/images/')
            updated = True
            
        if updated:
            await db.gallery.update_one(
                {"_id": item["_id"]}, 
                {"$set": {"before_image": item['before_image'], "after_image": item['after_image']}}
            )
            print(f"Updated gallery item: {item.get('title', 'Unknown')}")
    
    print("Gallery URLs fixed!")

async def fix_staff_urls():
    """Fix staff avatar URLs to use the new API route"""
    print("Fixing staff avatar URLs...")
    
    # Update staff avatars
    staff_members = await db.staff.find({}).to_list(length=None)
    
    for staff in staff_members:
        if staff.get('avatar_url') and '/uploads/avatars/' in staff['avatar_url']:
            staff['avatar_url'] = staff['avatar_url'].replace('/uploads/avatars/', '/api/uploads/avatars/')
            await db.staff.update_one(
                {"_id": staff["_id"]}, 
                {"$set": {"avatar_url": staff['avatar_url']}}
            )
            print(f"Updated staff avatar: {staff.get('name', 'Unknown')}")
    
    print("Staff avatar URLs fixed!")

async def fix_page_urls():
    """Fix page featured image URLs to use the new API route"""
    print("Fixing page featured image URLs...")
    
    # Update page featured images
    pages = await db.pages.find({}).to_list(length=None)
    
    for page in pages:
        updated = False
        
        # Fix featured_image URL
        if page.get('featured_image') and '/uploads/images/' in page['featured_image']:
            page['featured_image'] = page['featured_image'].replace('/uploads/images/', '/api/uploads/images/')
            updated = True
            
        # Fix any images in the images array
        if page.get('images'):
            for i, image_url in enumerate(page['images']):
                if '/uploads/images/' in image_url:
                    page['images'][i] = image_url.replace('/uploads/images/', '/api/uploads/images/')
                    updated = True
        
        # Fix any videos in the videos array
        if page.get('videos'):
            for i, video_url in enumerate(page['videos']):
                if '/uploads/videos/' in video_url:
                    page['videos'][i] = video_url.replace('/uploads/videos/', '/api/uploads/videos/')
                    updated = True
                    
        if updated:
            update_data = {}
            if page.get('featured_image'):
                update_data['featured_image'] = page['featured_image']
            if page.get('images'):
                update_data['images'] = page['images']
            if page.get('videos'):
                update_data['videos'] = page['videos']
                
            await db.pages.update_one(
                {"_id": page["_id"]}, 
                {"$set": update_data}
            )
            print(f"Updated page: {page.get('title', 'Unknown')}")
    
    print("Page URLs fixed!")

async def main():
    print("Starting URL fixes...")
    await fix_gallery_urls()
    await fix_staff_urls()
    await fix_page_urls()
    print("All URLs fixed!")
    
if __name__ == "__main__":
    asyncio.run(main())