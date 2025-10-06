from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile
from contextlib import asynccontextmanager
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, date, time, timedelta
import jwt
from passlib.context import CryptContext
import shutil
import mimetypes
import aiomysql

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'db': os.getenv('MYSQL_DATABASE', 'target_lafata'),
    'charset': 'utf8mb4',
    'autocommit': True
}

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
BACKEND_URL = "https://frisorlafata.dk"

# Global connection pool
pool = None

async def init_db():
    global pool
    pool = await aiomysql.create_pool(**DB_CONFIG)

async def close_db():
    global pool
    if pool:
        pool.close()
        await pool.wait_closed()

@asynccontextmanager
async def get_db_connection():
    global pool
    if not pool:
        await init_db()
    async with pool.acquire() as connection:
        yield connection

# Create the main app
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()

app = FastAPI(lifespan=lifespan, title="Frisor LaFata API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Create uploads directory
uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
(uploads_dir / "avatars").mkdir(exist_ok=True)
(uploads_dir / "images").mkdir(exist_ok=True)
(uploads_dir / "videos").mkdir(exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: Optional[str] = None
    email: str
    role: str = "user"
    created_at: Optional[datetime] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None

class Staff(BaseModel):
    id: Optional[str] = None
    name: str
    specialty: str
    experience: str
    avatar_url: Optional[str] = None
    available_hours: Optional[str] = None
    created_at: Optional[datetime] = None

class StaffCreate(BaseModel):
    name: str
    specialty: str
    experience: str
    avatar_url: Optional[str] = None
    available_hours: Optional[str] = None

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    experience: Optional[str] = None
    avatar_url: Optional[str] = None
    available_hours: Optional[str] = None

class Service(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    price: float
    duration: int
    category: str
    icon: str = "✨"
    created_at: Optional[datetime] = None

class ServiceCreate(BaseModel):
    name: str
    description: str
    price: float
    duration: int
    category: str
    icon: str = "✨"

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    duration: Optional[int] = None
    category: Optional[str] = None
    icon: Optional[str] = None

class Booking(BaseModel):
    id: Optional[str] = None
    customer_name: str
    customer_email: str
    customer_phone: str
    service_id: str
    staff_id: str
    date: date
    time: time
    status: str = "confirmed"
    notes: Optional[str] = None
    is_home_service: bool = False
    service_address: Optional[str] = None
    service_city: Optional[str] = None
    service_postal_code: Optional[str] = None
    travel_fee: float = 0.0
    special_instructions: Optional[str] = None
    created_at: Optional[datetime] = None

class BookingCreate(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: str
    service_id: str
    staff_id: str
    date: date
    time: time
    notes: Optional[str] = None
    is_home_service: bool = False
    service_address: Optional[str] = None
    service_city: Optional[str] = None
    service_postal_code: Optional[str] = None
    travel_fee: float = 0.0
    special_instructions: Optional[str] = None

class BookingUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    service_id: Optional[str] = None
    staff_id: Optional[str] = None
    date: Optional[date] = None
    time: Optional[time] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    is_home_service: Optional[bool] = None
    service_address: Optional[str] = None
    service_city: Optional[str] = None
    service_postal_code: Optional[str] = None
    travel_fee: Optional[float] = None
    special_instructions: Optional[str] = None

class Page(BaseModel):
    id: Optional[str] = None
    title: str
    slug: str
    content: str
    status: str = "published"
    meta_description: Optional[str] = None
    featured_image: Optional[str] = None
    page_type: str = "page"
    categories: List[str] = []
    tags: List[str] = []
    excerpt: Optional[str] = None
    images: List[str] = []
    videos: List[str] = []
    show_in_navigation: bool = True
    navigation_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PageCreate(BaseModel):
    title: str
    slug: str
    content: str
    status: str = "published"
    meta_description: Optional[str] = None
    featured_image: Optional[str] = None
    page_type: str = "page"
    categories: List[str] = []
    tags: List[str] = []
    excerpt: Optional[str] = None
    images: List[str] = []
    videos: List[str] = []
    show_in_navigation: bool = True
    navigation_order: int = 0

class PageUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    meta_description: Optional[str] = None
    featured_image: Optional[str] = None
    page_type: Optional[str] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    excerpt: Optional[str] = None
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    show_in_navigation: Optional[bool] = None
    navigation_order: Optional[int] = None

class GalleryItem(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    before_image: str
    after_image: str
    service_type: str
    staff_id: Optional[str] = None
    is_featured: bool = False
    created_at: Optional[datetime] = None

class GalleryItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    before_image: str
    after_image: str
    service_type: str
    staff_id: Optional[str] = None
    is_featured: bool = False

class GalleryItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    before_image: Optional[str] = None
    after_image: Optional[str] = None
    service_type: Optional[str] = None
    staff_id: Optional[str] = None
    is_featured: Optional[bool] = None

class SiteSettings(BaseModel):
    id: Optional[str] = None
    site_title: str = "Frisor LaFata"
    site_description: str = "Professional barbershop services"
    contact_email: str = "info@frisorlafata.dk"
    contact_phone: str = "+45 12 34 56 78"
    address: str = "Copenhagen, Denmark"
    opening_hours: str = "Mon-Fri: 9-18, Sat: 9-16"
    booking_system_enabled: bool = True
    home_service_enabled: bool = True
    home_service_fee: float = 150.0
    home_service_description: str = "Vi kommer til dig! Oplev professionel barbering i dit eget hjem."
    social_media_enabled: bool = True
    social_media_title: str = "Følg os på sociale medier"
    social_media_description: str = "Hold dig opdateret med vores seneste arbejde og tilbud"
    instagram_enabled: bool = True
    instagram_username: str = ""
    instagram_url: str = ""
    instagram_hashtag: str = ""
    instagram_embed_code: str = ""
    facebook_enabled: bool = True
    facebook_page_url: str = ""
    facebook_embed_code: str = ""
    tiktok_enabled: bool = True
    tiktok_username: str = ""
    tiktok_embed_code: str = ""
    twitter_enabled: bool = True
    twitter_username: str = ""
    twitter_embed_code: str = ""
    youtube_enabled: bool = True
    youtube_channel_url: str = ""
    youtube_embed_code: str = ""

class SettingsUpdate(BaseModel):
    site_title: Optional[str] = None
    site_description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    opening_hours: Optional[str] = None
    booking_system_enabled: Optional[bool] = None
    home_service_enabled: Optional[bool] = None
    home_service_fee: Optional[float] = None
    home_service_description: Optional[str] = None
    social_media_enabled: Optional[bool] = None
    social_media_title: Optional[str] = None
    social_media_description: Optional[str] = None
    instagram_enabled: Optional[bool] = None
    instagram_username: Optional[str] = None
    instagram_url: Optional[str] = None
    instagram_hashtag: Optional[str] = None
    instagram_embed_code: Optional[str] = None
    facebook_enabled: Optional[bool] = None
    facebook_page_url: Optional[str] = None
    facebook_embed_code: Optional[str] = None
    tiktok_enabled: Optional[bool] = None
    tiktok_username: Optional[str] = None
    tiktok_embed_code: Optional[str] = None
    twitter_enabled: Optional[bool] = None
    twitter_username: Optional[str] = None
    twitter_embed_code: Optional[str] = None
    youtube_enabled: Optional[bool] = None
    youtube_channel_url: Optional[str] = None
    youtube_embed_code: Optional[str] = None

class HomepageSection(BaseModel):
    id: Optional[str] = None
    section_type: str
    section_order: int
    is_enabled: bool = True
    title: str = ""
    subtitle: str = ""
    description: str = ""
    button_text: str = ""
    button_action: str = ""
    background_color: str = "#1a1a1a"
    text_color: str = "#d4af37"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class HomepageSectionUpdate(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = None
    button_text: Optional[str] = None
    button_action: Optional[str] = None
    background_color: Optional[str] = None
    text_color: Optional[str] = None
    is_enabled: Optional[bool] = None

class SectionReorderRequest(BaseModel):
    sections: List[Dict[str, Any]]

# Helper functions
def prepare_for_db(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value
            elif isinstance(value, date):
                data[key] = value
            elif isinstance(value, time):
                data[key] = value
            elif isinstance(value, list):
                data[key] = ','.join(map(str, value)) if value else ''
    return data

def prepare_from_db(record):
    if not record:
        return {}
    
    result = {}
    for key, value in record.items():
        if key in ['categories', 'tags', 'images', 'videos'] and isinstance(value, str):
            result[key] = [x.strip() for x in value.split(',') if x.strip()] if value else []
        else:
            result[key] = value
    
    return result

# Authentication functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        async with get_db_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                result = await cursor.fetchone()
                if not result:
                    raise HTTPException(status_code=401, detail="User not found")
                
                return User(**prepare_from_db(result))
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Auth endpoints
@api_router.post("/auth/login")
async def login(user_data: UserLogin):
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # Check users table
            await cursor.execute("SELECT * FROM users WHERE email = %s", (user_data.email,))
            result = await cursor.fetchone()
            
            if result:
                user = prepare_from_db(result)
                # Check password from user_passwords table
                await cursor.execute("SELECT password FROM user_passwords WHERE user_id = %s", (user['id'],))
                pwd_result = await cursor.fetchone()
                
                if pwd_result and verify_password(user_data.password, pwd_result['password']):
                    access_token = create_access_token(data={"sub": user['email']})
                    return {"access_token": access_token, "token_type": "bearer", "user": user}
            
            raise HTTPException(status_code=401, detail="Invalid email or password")

# User endpoints
@api_router.get("/users", response_model=List[User])
async def get_users(admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
            result = await cursor.fetchall()
            return [prepare_from_db(row) for row in result]

@api_router.post("/users", response_model=User)
async def create_user(user: UserCreate, admin_user: User = Depends(get_admin_user)):
    user_id = str(uuid.uuid4())
    
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            # Insert user
            user_data = prepare_for_db(user.dict())
            user_data['id'] = user_id
            user_data['created_at'] = datetime.now()
            
            await cursor.execute(
                "INSERT INTO users (id, email, role, created_at) VALUES (%s, %s, %s, %s)",
                (user_data['id'], user_data['email'], user_data['role'], user_data['created_at'])
            )
            
            # Insert password
            hashed_password = get_password_hash(user.password)
            await cursor.execute(
                "INSERT INTO user_passwords (user_id, password) VALUES (%s, %s)",
                (user_id, hashed_password)
            )
            
            await conn.commit()
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                result = await cursor.fetchone()
                return prepare_from_db(result)

@api_router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user: UserUpdate, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            update_fields = []
            values = []
            
            for field, value in user.dict(exclude_unset=True).items():
                update_fields.append(f"{field} = %s")
                values.append(value)
            
            if update_fields:
                values.append(user_id)
                query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                await cursor.execute(query, values)
                await conn.commit()
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                result = await cursor.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="User not found")
                return prepare_from_db(result)

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("DELETE FROM user_passwords WHERE user_id = %s", (user_id,))
            await cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            await conn.commit()
            return {"message": "User deleted successfully"}

# Staff endpoints
@api_router.get("/staff", response_model=List[Staff])
async def get_staff():
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM staff ORDER BY created_at DESC")
            result = await cursor.fetchall()
            return [prepare_from_db(row) for row in result]

@api_router.post("/staff", response_model=Staff)
async def create_staff(staff: StaffCreate, admin_user: User = Depends(get_admin_user)):
    staff_id = str(uuid.uuid4())
    
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            staff_data = prepare_for_db(staff.dict())
            staff_data['id'] = staff_id
            staff_data['created_at'] = datetime.now()
            
            await cursor.execute(
                "INSERT INTO staff (id, name, specialty, experience, avatar_url, available_hours, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (staff_data['id'], staff_data['name'], staff_data['specialty'], staff_data['experience'], 
                 staff_data.get('avatar_url'), staff_data.get('available_hours'), staff_data['created_at'])
            )
            await conn.commit()
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM staff WHERE id = %s", (staff_id,))
                result = await cursor.fetchone()
                return prepare_from_db(result)

@api_router.put("/staff/{staff_id}", response_model=Staff)
async def update_staff(staff_id: str, staff: StaffUpdate, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            update_fields = []
            values = []
            
            for field, value in staff.dict(exclude_unset=True).items():
                update_fields.append(f"{field} = %s")
                values.append(value)
            
            if update_fields:
                values.append(staff_id)
                query = f"UPDATE staff SET {', '.join(update_fields)} WHERE id = %s"
                await cursor.execute(query, values)
                await conn.commit()
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM staff WHERE id = %s", (staff_id,))
                result = await cursor.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Staff not found")
                return prepare_from_db(result)

@api_router.delete("/staff/{staff_id}")
async def delete_staff(staff_id: str, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("DELETE FROM staff WHERE id = %s", (staff_id,))
            await conn.commit()
            return {"message": "Staff deleted successfully"}

# Services endpoints
@api_router.get("/services", response_model=List[Service])
async def get_services():
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM services ORDER BY created_at DESC")
            result = await cursor.fetchall()
            return [prepare_from_db(row) for row in result]

@api_router.post("/services", response_model=Service)
async def create_service(service: ServiceCreate, admin_user: User = Depends(get_admin_user)):
    service_id = str(uuid.uuid4())
    
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            service_data = prepare_for_db(service.dict())
            service_data['id'] = service_id
            service_data['created_at'] = datetime.now()
            
            await cursor.execute(
                "INSERT INTO services (id, name, description, price, duration, category, icon, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (service_data['id'], service_data['name'], service_data['description'], service_data['price'], 
                 service_data['duration'], service_data['category'], service_data['icon'], service_data['created_at'])
            )
            await conn.commit()
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM services WHERE id = %s", (service_id,))
                result = await cursor.fetchone()
                return prepare_from_db(result)

@api_router.put("/services/{service_id}", response_model=Service)
async def update_service(service_id: str, service: ServiceUpdate, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            update_fields = []
            values = []
            
            for field, value in service.dict(exclude_unset=True).items():
                update_fields.append(f"{field} = %s")
                values.append(value)
            
            if update_fields:
                values.append(service_id)
                query = f"UPDATE services SET {', '.join(update_fields)} WHERE id = %s"
                await cursor.execute(query, values)
                await conn.commit()
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM services WHERE id = %s", (service_id,))
                result = await cursor.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Service not found")
                return prepare_from_db(result)

@api_router.delete("/services/{service_id}")
async def delete_service(service_id: str, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("DELETE FROM services WHERE id = %s", (service_id,))
            await conn.commit()
            return {"message": "Service deleted successfully"}

# Bookings endpoints
@api_router.get("/bookings", response_model=List[Booking])
async def get_bookings(admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM bookings ORDER BY date DESC, time DESC")
            result = await cursor.fetchall()
            return [prepare_from_db(row) for row in result]

@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking: BookingCreate):
    booking_id = str(uuid.uuid4())
    
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            booking_data = prepare_for_db(booking.dict())
            booking_data['id'] = booking_id
            booking_data['created_at'] = datetime.now()
            
            await cursor.execute(
                "INSERT INTO bookings (id, customer_name, customer_email, customer_phone, service_id, staff_id, date, time, status, notes, is_home_service, service_address, service_city, service_postal_code, travel_fee, special_instructions, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (booking_data['id'], booking_data['customer_name'], booking_data['customer_email'], booking_data['customer_phone'], 
                 booking_data['service_id'], booking_data['staff_id'], booking_data['date'], booking_data['time'], 
                 booking_data.get('status', 'confirmed'), booking_data.get('notes'), booking_data.get('is_home_service', False),
                 booking_data.get('service_address'), booking_data.get('service_city'), booking_data.get('service_postal_code'),
                 booking_data.get('travel_fee', 0.0), booking_data.get('special_instructions'), booking_data['created_at'])
            )
            await conn.commit()
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM bookings WHERE id = %s", (booking_id,))
                result = await cursor.fetchone()
                return prepare_from_db(result)

@api_router.put("/bookings/{booking_id}", response_model=Booking)
async def update_booking(booking_id: str, booking: BookingUpdate, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            update_fields = []
            values = []
            
            for field, value in booking.dict(exclude_unset=True).items():
                update_fields.append(f"{field} = %s")
                values.append(value)
            
            if update_fields:
                values.append(booking_id)
                query = f"UPDATE bookings SET {', '.join(update_fields)} WHERE id = %s"
                await cursor.execute(query, values)
                await conn.commit()
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM bookings WHERE id = %s", (booking_id,))
                result = await cursor.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Booking not found")
                return prepare_from_db(result)

@api_router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
            await conn.commit()
            return {"message": "Booking deleted successfully"}

# Gallery endpoints
@api_router.get("/gallery", response_model=List[GalleryItem])
async def get_gallery(featured_only: bool = False):
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            if featured_only:
                await cursor.execute("SELECT * FROM gallery WHERE is_featured = 1 ORDER BY created_at DESC")
            else:
                await cursor.execute("SELECT * FROM gallery ORDER BY created_at DESC")
            result = await cursor.fetchall()
            return [prepare_from_db(row) for row in result]

@api_router.post("/gallery", response_model=GalleryItem)
async def create_gallery_item(gallery_item: GalleryItemCreate, admin_user: User = Depends(get_admin_user)):
    item_id = str(uuid.uuid4())
    
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            item_data = prepare_for_db(gallery_item.dict())
            item_data['id'] = item_id
            item_data['created_at'] = datetime.now()
            
            await cursor.execute(
                "INSERT INTO gallery (id, title, description, before_image, after_image, service_type, staff_id, is_featured, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (item_data['id'], item_data['title'], item_data.get('description'), item_data['before_image'], 
                 item_data['after_image'], item_data['service_type'], item_data.get('staff_id'), 
                 item_data.get('is_featured', False), item_data['created_at'])
            )
            await conn.commit()
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM gallery WHERE id = %s", (item_id,))
                result = await cursor.fetchone()
                return prepare_from_db(result)

@api_router.put("/gallery/{item_id}", response_model=GalleryItem)
async def update_gallery_item(item_id: str, gallery_item: GalleryItemUpdate, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            update_fields = []
            values = []
            
            for field, value in gallery_item.dict(exclude_unset=True).items():
                update_fields.append(f"{field} = %s")
                values.append(value)
            
            if update_fields:
                values.append(item_id)
                query = f"UPDATE gallery SET {', '.join(update_fields)} WHERE id = %s"
                await cursor.execute(query, values)
                await conn.commit()
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM gallery WHERE id = %s", (item_id,))
                result = await cursor.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Gallery item not found")
                return prepare_from_db(result)

@api_router.delete("/gallery/{item_id}")
async def delete_gallery_item(item_id: str, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("DELETE FROM gallery WHERE id = %s", (item_id,))
            await conn.commit()
            return {"message": "Gallery item deleted successfully"}

# Pages endpoints
@api_router.get("/pages", response_model=List[Page])
async def get_pages(admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM pages ORDER BY navigation_order ASC, created_at DESC")
            result = await cursor.fetchall()
            return [prepare_from_db(row) for row in result]

@api_router.get("/public/pages")
async def get_public_pages():
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM pages WHERE status = 'published' AND show_in_navigation = 1 ORDER BY navigation_order ASC")
            result = await cursor.fetchall()
            return [prepare_from_db(row) for row in result]

@api_router.post("/pages", response_model=Page)
async def create_page(page: PageCreate, admin_user: User = Depends(get_admin_user)):
    page_id = str(uuid.uuid4())
    
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            page_data = prepare_for_db(page.dict())
            page_data['id'] = page_id
            page_data['created_at'] = datetime.now()
            page_data['updated_at'] = datetime.now()
            
            await cursor.execute(
                "INSERT INTO pages (id, title, slug, content, status, meta_description, featured_image, page_type, categories, tags, excerpt, images, videos, show_in_navigation, navigation_order, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (page_data['id'], page_data['title'], page_data['slug'], page_data['content'], 
                 page_data.get('status', 'published'), page_data.get('meta_description'), page_data.get('featured_image'),
                 page_data.get('page_type', 'page'), page_data.get('categories', ''), page_data.get('tags', ''),
                 page_data.get('excerpt'), page_data.get('images', ''), page_data.get('videos', ''),
                 page_data.get('show_in_navigation', True), page_data.get('navigation_order', 0),
                 page_data['created_at'], page_data['updated_at'])
            )
            await conn.commit()
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM pages WHERE id = %s", (page_id,))
                result = await cursor.fetchone()
                return prepare_from_db(result)

@api_router.put("/pages/{page_id}", response_model=Page)
async def update_page(page_id: str, page: PageUpdate, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            update_fields = []
            values = []
            
            page_data = prepare_for_db(page.dict(exclude_unset=True))
            page_data['updated_at'] = datetime.now()
            
            for field, value in page_data.items():
                update_fields.append(f"{field} = %s")
                values.append(value)
            
            if update_fields:
                values.append(page_id)
                query = f"UPDATE pages SET {', '.join(update_fields)} WHERE id = %s"
                await cursor.execute(query, values)
                await conn.commit()
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM pages WHERE id = %s", (page_id,))
                result = await cursor.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Page not found")
                return prepare_from_db(result)

@api_router.delete("/pages/{page_id}")
async def delete_page(page_id: str, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("DELETE FROM pages WHERE id = %s", (page_id,))
            await conn.commit()
            return {"message": "Page deleted successfully"}

# Homepage sections endpoints
@api_router.get("/homepage/sections", response_model=List[HomepageSection])
async def get_homepage_sections(admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM homepage_sections ORDER BY section_order ASC")
            result = await cursor.fetchall()
            
            if not result:
                # Create default sections
                default_sections = [
                    {"id": str(uuid.uuid4()), "section_type": "hero", "section_order": 1, "is_enabled": True, "title": "Velkommen til Frisør LaFata", "subtitle": "Klassisk Barbering", "description": "Professionel barbering i hjertet af byen"},
                    {"id": str(uuid.uuid4()), "section_type": "services", "section_order": 2, "is_enabled": True, "title": "Vores Tjenester", "subtitle": "", "description": "Udforsk vores udvalg af professionelle barber-tjenester"},
                    {"id": str(uuid.uuid4()), "section_type": "staff", "section_order": 3, "is_enabled": True, "title": "Mød Vores Team", "subtitle": "", "description": "Vores erfarne barbere er klar til at give dig den bedste service"},
                    {"id": str(uuid.uuid4()), "section_type": "gallery", "section_order": 4, "is_enabled": True, "title": "Galleri", "subtitle": "", "description": "Se eksempler på vores arbejde"},
                    {"id": str(uuid.uuid4()), "section_type": "social", "section_order": 5, "is_enabled": False, "title": "Følg Os", "subtitle": "", "description": "Hold dig opdateret på sociale medier"},
                    {"id": str(uuid.uuid4()), "section_type": "contact", "section_order": 6, "is_enabled": True, "title": "Kontakt Os", "subtitle": "", "description": "Book din tid i dag"}
                ]
                
                for section in default_sections:
                    section['created_at'] = datetime.now()
                    section['updated_at'] = datetime.now()
                    await cursor.execute(
                        "INSERT INTO homepage_sections (id, section_type, section_order, is_enabled, title, subtitle, description, button_text, button_action, background_color, text_color, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (section['id'], section['section_type'], section['section_order'], section['is_enabled'], 
                         section['title'], section['subtitle'], section['description'], '', '', '#1a1a1a', '#d4af37',
                         section['created_at'], section['updated_at'])
                    )
                await conn.commit()
                
                await cursor.execute("SELECT * FROM homepage_sections ORDER BY section_order ASC")
                result = await cursor.fetchall()
            
            return [prepare_from_db(row) for row in result]

@api_router.get("/public/homepage/sections")
async def get_public_homepage_sections():
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM homepage_sections WHERE is_enabled = 1 ORDER BY section_order ASC")
            result = await cursor.fetchall()
            return [prepare_from_db(row) for row in result]

@api_router.put("/homepage/sections/{section_id}", response_model=HomepageSection)
async def update_homepage_section(section_id: str, section: HomepageSectionUpdate, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            update_fields = []
            values = []
            
            section_data = section.dict(exclude_unset=True)
            section_data['updated_at'] = datetime.now()
            
            for field, value in section_data.items():
                update_fields.append(f"{field} = %s")
                values.append(value)
            
            if update_fields:
                values.append(section_id)
                query = f"UPDATE homepage_sections SET {', '.join(update_fields)} WHERE id = %s"
                await cursor.execute(query, values)
                await conn.commit()
            
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM homepage_sections WHERE id = %s", (section_id,))
                result = await cursor.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail="Section not found")
                return prepare_from_db(result)

@api_router.put("/homepage/sections/reorder")
async def reorder_homepage_sections(request: SectionReorderRequest, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor() as cursor:
            for section in request.sections:
                await cursor.execute(
                    "UPDATE homepage_sections SET section_order = %s WHERE id = %s",
                    (section['section_order'], section['id'])
                )
            await conn.commit()
            return {"message": "Sections reordered successfully"}

# Settings endpoints
@api_router.get("/settings", response_model=SiteSettings)
async def get_settings(admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM settings LIMIT 1")
            result = await cursor.fetchone()
            if result:
                return prepare_from_db(result)
            else:
                # Create default settings
                settings_id = str(uuid.uuid4())
                default_settings = {
                    'id': settings_id,
                    'site_title': 'Frisor LaFata',
                    'site_description': 'Professional barbershop services',
                    'contact_email': 'info@frisorlafata.dk',
                    'contact_phone': '+45 12 34 56 78',
                    'address': 'Copenhagen, Denmark',
                    'opening_hours': 'Mon-Fri: 9-18, Sat: 9-16',
                    'booking_system_enabled': 1,
                    'home_service_enabled': 1,
                    'home_service_fee': 150.0,
                    'home_service_description': 'Vi kommer til dig! Oplev professionel barbering i dit eget hjem.',
                    'social_media_enabled': 0,
                    'social_media_title': 'Følg os på sociale medier',
                    'social_media_description': 'Hold dig opdateret med vores seneste arbejde og tilbud',
                    'instagram_enabled': 0,
                    'facebook_enabled': 0,
                    'tiktok_enabled': 0,
                    'twitter_enabled': 0,
                    'youtube_enabled': 0
                }
                
                columns = ', '.join(default_settings.keys())
                placeholders = ', '.join(['%s'] * len(default_settings))
                await cursor.execute(
                    f"INSERT INTO settings ({columns}) VALUES ({placeholders})",
                    tuple(default_settings.values())
                )
                await conn.commit()
                return prepare_from_db(default_settings)

@api_router.put("/settings", response_model=SiteSettings)
async def update_settings(settings: SettingsUpdate, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM settings LIMIT 1")
            result = await cursor.fetchone()
            
            if result:
                update_fields = []
                values = []
                
                for field, value in settings.dict(exclude_unset=True).items():
                    update_fields.append(f"{field} = %s")
                    values.append(value)
                
                if update_fields:
                    values.append(result['id'])
                    query = f"UPDATE settings SET {', '.join(update_fields)} WHERE id = %s"
                    await cursor.execute(query, values)
                    await conn.commit()
                
                await cursor.execute("SELECT * FROM settings WHERE id = %s", (result['id'],))
                updated_result = await cursor.fetchone()
                return prepare_from_db(updated_result)
            else:
                raise HTTPException(status_code=404, detail="Settings not found")

@api_router.get("/public/settings")
async def get_public_settings():
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM settings LIMIT 1")
            result = await cursor.fetchone()
            if result:
                settings = prepare_from_db(result)
                return {
                    'site_title': settings.get('site_title', 'Frisor LaFata'),
                    'site_description': settings.get('site_description', 'Professional barbershop services'),
                    'contact_email': settings.get('contact_email', 'info@frisorlafata.dk'),
                    'contact_phone': settings.get('contact_phone', '+45 12 34 56 78'),
                    'address': settings.get('address', 'Copenhagen, Denmark'),
                    'opening_hours': settings.get('opening_hours', 'Mon-Fri: 9-18, Sat: 9-16'),
                    'booking_system_enabled': settings.get('booking_system_enabled', 1),
                    'home_service_enabled': settings.get('home_service_enabled', 1),
                    'home_service_fee': settings.get('home_service_fee', 150.0),
                    'home_service_description': settings.get('home_service_description', 'Vi kommer til dig! Oplev professionel barbering i dit eget hjem.'),
                    'social_media_enabled': settings.get('social_media_enabled', 0),
                    'social_media_title': settings.get('social_media_title', 'Følg os på sociale medier'),
                    'social_media_description': settings.get('social_media_description', 'Hold dig opdateret med vores seneste arbejde og tilbud'),
                    'instagram_enabled': settings.get('instagram_enabled', 0),
                    'instagram_username': settings.get('instagram_username', ''),
                    'instagram_url': settings.get('instagram_url', ''),
                    'instagram_hashtag': settings.get('instagram_hashtag', ''),
                    'instagram_embed_code': settings.get('instagram_embed_code', ''),
                    'facebook_enabled': settings.get('facebook_enabled', 0),
                    'facebook_page_url': settings.get('facebook_page_url', ''),
                    'facebook_embed_code': settings.get('facebook_embed_code', ''),
                    'tiktok_enabled': settings.get('tiktok_enabled', 0),
                    'tiktok_username': settings.get('tiktok_username', ''),
                    'tiktok_embed_code': settings.get('tiktok_embed_code', ''),
                    'twitter_enabled': settings.get('twitter_enabled', 0),
                    'twitter_username': settings.get('twitter_username', ''),
                    'twitter_embed_code': settings.get('twitter_embed_code', ''),
                    'youtube_enabled': settings.get('youtube_enabled', 0),
                    'youtube_channel_url': settings.get('youtube_channel_url', ''),
                    'youtube_embed_code': settings.get('youtube_embed_code', '')
                }
            return {}

# File upload endpoints
@api_router.post("/upload/avatar")
async def upload_avatar(file: UploadFile = File(...), admin_user: User = Depends(get_admin_user)):
    if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    file_extension = file.filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = uploads_dir / "avatars" / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"url": f"{BACKEND_URL}/uploads/avatars/{filename}"}

@api_router.post("/upload/image")
async def upload_image(file: UploadFile = File(...), admin_user: User = Depends(get_admin_user)):
    if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    file_extension = file.filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = uploads_dir / "images" / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"url": f"{BACKEND_URL}/uploads/images/{filename}"}

@api_router.post("/upload/video")
async def upload_video(file: UploadFile = File(...), admin_user: User = Depends(get_admin_user)):
    if file.content_type not in ["video/mp4", "video/webm", "video/ogg", "video/avi", "video/mov"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    file_extension = file.filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = uploads_dir / "videos" / filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"url": f"{BACKEND_URL}/uploads/videos/{filename}"}

# Available slots endpoint
@api_router.get("/bookings/available-slots")
async def get_available_slots(date: str, staff_id: str):
    try:
        booking_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    async with get_db_connection() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT time FROM bookings WHERE date = %s AND staff_id = %s",
                (booking_date, staff_id)
            )
            booked_times = [row['time'] for row in await cursor.fetchall()]
            
            # Generate available slots (9:00 to 17:00, 30-minute intervals)
            available_slots = []
            start_time = time(9, 0)
            end_time = time(17, 0)
            current_time = start_time
            
            while current_time < end_time:
                if current_time not in booked_times:
                    available_slots.append(current_time.strftime('%H:%M'))
                
                # Add 30 minutes
                current_datetime = datetime.combine(booking_date, current_time)
                current_datetime += timedelta(minutes=30)
                current_time = current_datetime.time()
            
            return {"available_slots": available_slots}

# Root endpoints
@app.get("/")
async def root():
    return {"message": "Frisor LaFata API", "status": "running"}

@app.get("/api")
async def api_root():
    return {"message": "Frisor LaFata API v1.0", "endpoints": ["auth", "users", "staff", "services", "bookings", "settings", "pages", "gallery", "homepage"]}

# Include API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)