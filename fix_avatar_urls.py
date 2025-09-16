#!/usr/bin/env python3
"""
Script to fix avatar URLs in the database
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def fix_avatar_urls():
    """Fix all avatar URLs in the database"""
    
    # Correct base URL
    correct_base_url = "https://frisor-admin.preview.emergentagent.com"
    
    # Find all staff with avatar URLs
    staff_with_avatars = await db.staff.find({"avatar_url": {"$exists": True, "$ne": ""}}).to_list(length=None)
    
    print(f"Found {len(staff_with_avatars)} staff members with avatars")
    
    for staff in staff_with_avatars:
        old_url = staff.get('avatar_url', '')
        print(f"Staff: {staff['name']}")
        print(f"  Old URL: {old_url}")
        
        if old_url and 'localhost:8000' in old_url:
            # Extract the filename from the old URL
            filename = old_url.split('/')[-1]
            # Construct the new URL
            new_url = f"{correct_base_url}/uploads/avatars/{filename}"
            
            # Update the staff record
            await db.staff.update_one(
                {"id": staff["id"]},
                {"$set": {"avatar_url": new_url}}
            )
            print(f"  New URL: {new_url}")
            print(f"  Updated successfully!")
        else:
            print(f"  URL is already correct or empty")
        print()

if __name__ == "__main__":
    asyncio.run(fix_avatar_urls())