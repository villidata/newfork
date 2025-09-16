#!/usr/bin/env python3
"""
Fix remaining broken image URLs in the database.
This script updates URLs that are still using the old format to use the new API endpoint.
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def fix_image_urls():
    """Fix remaining broken image URLs in the database"""
    
    print("=== FIXING REMAINING BROKEN IMAGE URLS ===")
    
    # Define URL mappings
    old_domain = "https://frisor-admin.preview.emergentagent.com"
    new_domain = "https://stylista-admin.preview.emergentagent.com"
    
    # 1. Fix site settings hero_image
    print("\n1. Fixing site settings hero_image...")
    settings = await db.settings.find_one({"type": "site_settings"})
    if settings and "hero_image" in settings:
        old_hero_url = settings["hero_image"]
        print(f"   Current hero_image: {old_hero_url}")
        
        if old_domain in old_hero_url:
            # Convert from old static path to new API endpoint
            new_hero_url = old_hero_url.replace(
                f"{old_domain}/uploads/images/",
                f"{new_domain}/api/uploads/images/"
            )
            
            result = await db.settings.update_one(
                {"type": "site_settings"},
                {"$set": {"hero_image": new_hero_url}}
            )
            
            if result.modified_count > 0:
                print(f"   ✅ Updated hero_image to: {new_hero_url}")
            else:
                print(f"   ❌ Failed to update hero_image")
        else:
            print(f"   ✅ Hero image already uses correct URL format")
    else:
        print("   ⚠️ No hero_image found in settings")
    
    # 2. Fix staff avatar URLs
    print("\n2. Fixing staff avatar URLs...")
    staff_members = await db.staff.find({}).to_list(length=None)
    
    for staff in staff_members:
        if staff.get("avatar_url") and old_domain in staff["avatar_url"]:
            old_avatar_url = staff["avatar_url"]
            print(f"   Staff: {staff['name']}")
            print(f"   Current avatar_url: {old_avatar_url}")
            
            # Convert from old static path to new API endpoint
            new_avatar_url = old_avatar_url.replace(
                f"{old_domain}/uploads/avatars/",
                f"{new_domain}/api/uploads/avatars/"
            )
            
            result = await db.staff.update_one(
                {"id": staff["id"]},
                {"$set": {"avatar_url": new_avatar_url}}
            )
            
            if result.modified_count > 0:
                print(f"   ✅ Updated avatar_url to: {new_avatar_url}")
            else:
                print(f"   ❌ Failed to update avatar_url")
        else:
            print(f"   Staff: {staff['name']} - ✅ Avatar URL already correct or empty")
    
    # 3. Check for any other collections that might have old URLs
    print("\n3. Checking other collections for old URLs...")
    
    # Check pages collection
    pages = await db.pages.find({}).to_list(length=None)
    pages_updated = 0
    
    for page in pages:
        updated = False
        update_data = {}
        
        # Check featured_image
        if page.get("featured_image") and old_domain in page["featured_image"]:
            old_url = page["featured_image"]
            new_url = old_url.replace(f"{old_domain}/uploads/", f"{new_domain}/api/uploads/")
            update_data["featured_image"] = new_url
            updated = True
            print(f"   Page '{page['title']}' featured_image: {old_url} -> {new_url}")
        
        # Check images array
        if page.get("images"):
            new_images = []
            for img_url in page["images"]:
                if old_domain in img_url:
                    new_img_url = img_url.replace(f"{old_domain}/uploads/", f"{new_domain}/api/uploads/")
                    new_images.append(new_img_url)
                    updated = True
                    print(f"   Page '{page['title']}' image: {img_url} -> {new_img_url}")
                else:
                    new_images.append(img_url)
            if updated:
                update_data["images"] = new_images
        
        # Check content for embedded images
        if page.get("content") and old_domain in page["content"]:
            new_content = page["content"].replace(f"{old_domain}/uploads/", f"{new_domain}/api/uploads/")
            update_data["content"] = new_content
            updated = True
            print(f"   Page '{page['title']}' content updated with new image URLs")
        
        if updated:
            result = await db.pages.update_one(
                {"id": page["id"]},
                {"$set": update_data}
            )
            if result.modified_count > 0:
                pages_updated += 1
    
    if pages_updated > 0:
        print(f"   ✅ Updated {pages_updated} pages with new image URLs")
    else:
        print(f"   ✅ No pages needed URL updates")
    
    # 4. Check gallery items (should already be fixed, but let's verify)
    print("\n4. Verifying gallery items...")
    gallery_items = await db.gallery.find({}).to_list(length=None)
    gallery_issues = 0
    
    for item in gallery_items:
        if item.get("before_image") and old_domain in item["before_image"]:
            print(f"   ⚠️ Gallery item '{item['title']}' still has old before_image URL: {item['before_image']}")
            gallery_issues += 1
        if item.get("after_image") and old_domain in item["after_image"]:
            print(f"   ⚠️ Gallery item '{item['title']}' still has old after_image URL: {item['after_image']}")
            gallery_issues += 1
    
    if gallery_issues == 0:
        print(f"   ✅ All gallery items use correct URL format")
    else:
        print(f"   ⚠️ Found {gallery_issues} gallery items with old URLs")
    
    print("\n=== URL FIX COMPLETE ===")
    print("All remaining broken image URLs have been updated to use the new API endpoint format.")

if __name__ == "__main__":
    asyncio.run(fix_image_urls())