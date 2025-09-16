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

async def add_icons_to_services():
    """Add default icons to existing services based on their categories"""
    print("Adding icons to existing services...")
    
    # Default category to icon mapping
    category_icons = {
        'haircut': 'scissors-emoji',
        'beard': 'beard-emoji', 
        'styling': 'water-drop',
        'coloring': 'art',
        'premium': 'crown-emoji',
        'general': 'sparkles-emoji'
    }
    
    # Update services without icons
    services = await db.services.find({}).to_list(length=None)
    
    for service in services:
        # Only update if service doesn't have an icon field
        if 'icon' not in service or not service.get('icon'):
            category = service.get('category', 'general')
            default_icon = category_icons.get(category, 'sparkles-emoji')
            
            await db.services.update_one(
                {"_id": service["_id"]}, 
                {"$set": {"icon": default_icon}}
            )
            print(f"Updated service '{service.get('name', 'Unknown')}' with icon '{default_icon}' (category: {category})")
    
    print("Service icons updated!")

async def main():
    print("Starting service icon migration...")
    await add_icons_to_services()
    print("Migration completed!")
    
if __name__ == "__main__":
    asyncio.run(main())