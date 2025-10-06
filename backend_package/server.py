from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile
from contextlib import asynccontextmanager
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, date, time, timedelta
import jwt
from passlib.context import CryptContext
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import paypalrestsdk
import shutil
import mimetypes
from database import (
    init_db, close_db, get_db_connection, execute_query, 
    insert_record, update_record, delete_record,
    prepare_record_for_response, prepare_data_for_insert
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
# Use the frontend's backend URL for constructing image URLs
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')

# Email configuration (will be configurable from admin)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'email': os.environ.get('EMAIL_USER', ''),
    'password': os.environ.get('EMAIL_PASSWORD', ''),
    'from_name': 'Frisor LaFata'
}

# PayPal configuration
PAYPAL_CONFIG = {
    'client_id': os.environ.get('PAYPAL_CLIENT_ID', 'sandbox_client_id'),
    'client_secret': os.environ.get('PAYPAL_CLIENT_SECRET', 'sandbox_secret'),
    'sandbox_mode': os.environ.get('PAYPAL_SANDBOX_MODE', 'true').lower() == 'true'
}

# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": "sandbox" if PAYPAL_CONFIG['sandbox_mode'] else "live",
    "client_id": PAYPAL_CONFIG['client_id'],
    "client_secret": PAYPAL_CONFIG['client_secret']
})

# Create the main app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize MySQL database (temporarily disabled until MySQL is properly configured)
    # await init_db()
    yield
    # Close MySQL database
    # await close_db()

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

# Helper functions
def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, date):
                data[key] = value.isoformat()
            elif isinstance(value, time):
                data[key] = value.strftime('%H:%M:%S')
    return data

def parse_from_mongo(item):
    """Parse datetime strings back from MongoDB"""
    if isinstance(item, dict):
        for key, value in item.items():
            if key.endswith('_date') and isinstance(value, str):
                try:
                    item[key] = datetime.fromisoformat(value).date()
                except:
                    pass
            elif key.endswith('_time') and isinstance(value, str):
                try:
                    item[key] = datetime.strptime(value, '%H:%M:%S').time()
                except:
                    pass
            elif key.endswith('_datetime') and isinstance(value, str):
                try:
                    item[key] = datetime.fromisoformat(value)
                except:
                    pass
    return item

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Models
class StaffBreak(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    staff_id: str
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    break_type: str = "break"  # "break", "lunch", "meeting", "vacation", "sick", "other"
    reason: str = ""
    is_recurring: bool = False
    recurring_days: List[str] = Field(default_factory=list)  # ["monday", "tuesday", etc.]
    created_by: str  # user_id who created the break
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StaffBreakCreate(BaseModel):
    staff_id: str
    start_date: date
    end_date: date
    start_time: time
    end_time: time
    break_type: str = "break"
    reason: str = ""
    is_recurring: bool = False
    recurring_days: List[str] = Field(default_factory=list)

class StaffBreakUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_type: Optional[str] = None
    reason: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurring_days: Optional[List[str]] = None

class GalleryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    before_image: str
    after_image: str
    service_type: str = ""  # "haircut", "beard", "styling", etc.
    staff_id: Optional[str] = None
    is_featured: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GalleryItemCreate(BaseModel):
    title: str
    description: str = ""
    before_image: str
    after_image: str
    service_type: str = ""
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

class UserCreate(BaseModel):
    email: str
    password: str
    name: str = ""
    is_admin: bool = False
    role: str = "staff"  # "admin", "staff", "manager"

class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    is_admin: Optional[bool] = None
    role: Optional[str] = None

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: str
    is_admin: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Staff(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    bio: str = ""
    experience_years: int = 0
    specialties: List[str] = Field(default_factory=list)
    phone: str = ""
    email: str = ""
    avatar_url: str = ""
    portfolio_images: List[str] = Field(default_factory=list)
    # Social Media Links
    instagram_url: str = ""
    facebook_url: str = ""
    tiktok_url: str = ""
    linkedin_url: str = ""
    twitter_url: str = ""
    youtube_url: str = ""
    website_url: str = ""
    available_hours: dict = Field(default_factory=lambda: {
        "monday": {"start": "09:00", "end": "18:00", "enabled": True},
        "tuesday": {"start": "09:00", "end": "18:00", "enabled": True},
        "wednesday": {"start": "09:00", "end": "18:00", "enabled": True},
        "thursday": {"start": "09:00", "end": "18:00", "enabled": True},
        "friday": {"start": "09:00", "end": "18:00", "enabled": True},
        "saturday": {"start": "10:00", "end": "16:00", "enabled": True},
        "sunday": {"start": None, "end": None, "enabled": False}
    })
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StaffCreate(BaseModel):
    name: str
    bio: str = ""
    experience_years: int = 0
    specialties: List[str] = Field(default_factory=list)
    phone: str = ""
    email: str = ""
    avatar_url: str = ""
    portfolio_images: List[str] = Field(default_factory=list)
    # Social Media Links
    instagram_url: str = ""
    facebook_url: str = ""
    tiktok_url: str = ""
    linkedin_url: str = ""
    twitter_url: str = ""
    youtube_url: str = ""
    website_url: str = ""
    available_hours: dict = Field(default_factory=lambda: {
        "monday": {"start": "09:00", "end": "18:00", "enabled": True},
        "tuesday": {"start": "09:00", "end": "18:00", "enabled": True},
        "wednesday": {"start": "09:00", "end": "18:00", "enabled": True},
        "thursday": {"start": "09:00", "end": "18:00", "enabled": True},
        "friday": {"start": "09:00", "end": "18:00", "enabled": True},
        "saturday": {"start": "10:00", "end": "16:00", "enabled": True},
        "sunday": {"start": None, "end": None, "enabled": False}
    })

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    experience_years: Optional[int] = None
    specialties: Optional[List[str]] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    portfolio_images: Optional[List[str]] = None
    # Social Media Links
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    tiktok_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    youtube_url: Optional[str] = None
    website_url: Optional[str] = None
    available_hours: Optional[dict] = None

class Service(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    duration_minutes: int
    price: float
    description: str = ""
    category: str = "general"
    icon: str = "✨"  # Default emoji icon
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ServiceCreate(BaseModel):
    name: str
    duration_minutes: int
    price: float
    description: str = ""
    category: str = "general"
    icon: str = "✨"

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    customer_name: Optional[str] = ""
    customer_email: Optional[str] = ""
    customer_phone: Optional[str] = ""
    staff_id: str
    services: List[str]  # List of service IDs
    booking_date: date
    booking_time: time
    total_duration: int
    total_price: float
    payment_method: str = "cash"  # "cash", "paypal"
    payment_status: str = "pending"  # "pending", "paid", "cancelled"
    status: str = "pending"  # "pending", "confirmed", "cancelled", "completed", "rescheduled"
    notes: str = ""
    admin_notes: str = ""
    # Home service fields
    is_home_service: bool = False
    service_address: Optional[str] = ""
    service_city: Optional[str] = ""
    service_postal_code: Optional[str] = ""
    travel_fee: float = 0.00
    special_instructions: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BookingCreate(BaseModel):
    customer_id: str
    customer_name: Optional[str] = ""
    customer_email: Optional[str] = ""
    customer_phone: Optional[str] = ""
    staff_id: str
    services: List[str]
    booking_date: date
    booking_time: time
    payment_method: str = "cash"
    notes: str = ""
    # Home service fields
    is_home_service: bool = False
    service_address: Optional[str] = ""
    service_city: Optional[str] = ""
    service_postal_code: Optional[str] = ""
    special_instructions: Optional[str] = ""

class BookingUpdate(BaseModel):
    booking_date: Optional[date] = None
    booking_time: Optional[time] = None
    staff_id: Optional[str] = None
    status: Optional[str] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None
    admin_notes: Optional[str] = None

# Corporate booking models
class EmployeeService(BaseModel):
    employee_name: str
    service_ids: List[str]  # List of service IDs for this employee
    notes: Optional[str] = ""

class CorporateBooking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # Company information
    company_name: str
    company_contact_person: str
    company_email: str
    company_phone: str
    company_address: str
    company_city: str
    company_postal_code: str
    # Booking details
    staff_id: str
    booking_date: date
    booking_time: time
    # Employee services
    employees: List[EmployeeService]
    total_employees: int
    # Pricing
    company_travel_fee: float  # Extra cost for coming to company
    total_services_price: float
    total_price: float
    # Status and payment
    payment_method: str = "invoice"  # "invoice", "cash", "paypal"
    payment_status: str = "pending"  # "pending", "paid", "cancelled"
    status: str = "pending"  # "pending", "confirmed", "cancelled", "completed"
    # Additional information
    special_requirements: str = ""
    admin_notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CorporateBookingCreate(BaseModel):
    # Company information
    company_name: str
    company_contact_person: str
    company_email: str
    company_phone: str
    company_address: str
    company_city: str
    company_postal_code: str
    # Booking details
    staff_id: str
    booking_date: date
    booking_time: time
    # Employee services
    employees: List[EmployeeService]
    # Pricing
    company_travel_fee: float
    # Payment and additional info
    payment_method: str = "invoice"
    special_requirements: str = ""

class CorporateBookingUpdate(BaseModel):
    booking_date: Optional[date] = None
    booking_time: Optional[time] = None
    staff_id: Optional[str] = None
    status: Optional[str] = None
    payment_status: Optional[str] = None
    special_requirements: Optional[str] = None
    admin_notes: Optional[str] = None

class EmailTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    subject: str
    content: str
    language: str = "da"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    content: str
    language: str = "da"

class Page(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    slug: str
    content: str
    meta_description: str = ""
    is_published: bool = True
    show_in_navigation: bool = True
    navigation_order: int = 0
    page_type: str = "page"  # "page", "blog", "about", "service"
    featured_image: str = ""
    images: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    excerpt: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PageCreate(BaseModel):
    title: str
    slug: str
    content: str
    meta_description: str = ""
    is_published: bool = True
    show_in_navigation: bool = True
    navigation_order: int = 0
    page_type: str = "page"
    featured_image: str = ""
    images: List[str] = Field(default_factory=list)
    videos: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    excerpt: str = ""

class PageUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: Optional[bool] = None
    show_in_navigation: Optional[bool] = None
    navigation_order: Optional[int] = None
    page_type: Optional[str] = None
    featured_image: Optional[str] = None
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    excerpt: Optional[str] = None

class SiteSettings(BaseModel):
    site_title: str = "Frisor LaFata"
    site_description: str = "Klassisk barbering siden 2010"
    contact_phone: str = "+45 12 34 56 78"
    contact_email: str = "info@frisorlafata.dk"
    address: str = "Hovedgaden 123, 1000 København"
    hero_title: str = "Klassisk Barbering"
    hero_subtitle: str = "i Hjertet af Byen"
    hero_description: str = "Oplev den autentiske barber-oplevelse hos Frisor LaFata."
    hero_image: str = ""
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_sandbox_mode: bool = True
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_user: str = ""
    email_password: str = ""
    # Email Templates
    email_subject_template: str = "Booking Confirmation - {{business_name}}"
    email_body_template: str = """Dear {{customer_name}},

Thank you for booking with {{business_name}}!

Booking Details:
- Date: {{booking_date}}
- Time: {{booking_time}}
- Services: {{services}}
- Staff: {{staff_name}}
- Total Price: {{total_price}} DKK

Location:
{{business_address}}

Phone: {{business_phone}}
Email: {{business_email}}

We look forward to seeing you!

Best regards,
{{business_name}} Team"""
    # Social Media Settings
    social_media_enabled: bool = True
    social_media_title: str = "Follow Us"
    social_media_description: str = "Se vores seneste arbejde og tilbud på sociale medier"
    # Instagram
    instagram_enabled: bool = True
    instagram_username: str = ""
    instagram_hashtag: str = ""
    instagram_embed_code: str = ""
    # Facebook
    facebook_enabled: bool = True
    facebook_page_url: str = ""
    facebook_embed_code: str = ""
    # TikTok
    tiktok_enabled: bool = False
    tiktok_username: str = ""
    tiktok_embed_code: str = ""
    # Twitter/X
    twitter_enabled: bool = False
    twitter_username: str = ""
    twitter_embed_code: str = ""
    # YouTube
    youtube_enabled: bool = False
    youtube_channel_url: str = ""
    youtube_embed_code: str = ""
    # Booking System Settings
    booking_system_enabled: bool = True
    home_service_enabled: bool = True
    home_service_fee: float = 150.00
    home_service_description: str = "Vi kommer til dig! Oplev professionel barbering i dit eget hjem."
    # Booking Reminder Email Template
    reminder_subject_template: str = "Appointment Reminder - {{business_name}}"
    reminder_body_template: str = """Dear {{customer_name}},

This is a friendly reminder about your upcoming appointment with {{business_name}}.

Appointment Details:
- Date: {{booking_date}}
- Time: {{booking_time}}
- Services: {{services}}
- Staff: {{staff_name}}
- Total Price: {{total_price}} DKK

Location:
{{business_address}}

Phone: {{business_phone}}

Please arrive 5 minutes early. If you need to cancel or reschedule, please contact us as soon as possible.

We look forward to seeing you!

Best regards,
{{business_name}} Team"""
    # Booking Confirmation Email Template
    email_confirmation_subject: str = "Booking Confirmed - {{business_name}}"
    email_confirmation_body: str = """Dear {{customer_name}},

Great news! Your booking has been CONFIRMED.

Confirmed Booking Details:
- Date: {{booking_date}}
- Time: {{booking_time}}
- Services: {{services}}
- Staff: {{staff_name}}
- Total Price: {{total_price}} DKK

Location:
{{business_address}}

Phone: {{business_phone}}
Email: {{business_email}}

We look forward to seeing you at the confirmed time!

Best regards,
{{business_name}} Team"""
    # Booking Change Email Template
    email_change_subject: str = "Booking Time Changed - {{business_name}}"
    email_change_body: str = """Dear {{customer_name}},

We need to inform you about a change to your booking.

UPDATED Booking Details:
- NEW Date: {{booking_date}}
- NEW Time: {{booking_time}}
- Services: {{services}} (unchanged)
- Staff: {{staff_name}}
- Total Price: {{total_price}} DKK (unchanged)

{{#if admin_notes}}
Reason for change: {{admin_notes}}
{{/if}}

Location:
{{business_address}}

Phone: {{business_phone}}
Email: {{business_email}}

We apologize for any inconvenience and look forward to seeing you at the new time!

Best regards,
{{business_name}} Team"""

# Business hours configuration
BUSINESS_HOURS = {
    "monday": {"start": "09:00", "end": "18:00"},
    "tuesday": {"start": "09:00", "end": "18:00"},
    "wednesday": {"start": "09:00", "end": "18:00"},
    "thursday": {"start": "09:00", "end": "18:00"},
    "friday": {"start": "09:00", "end": "18:00"},
    "saturday": {"start": "09:00", "end": "16:00"},
    "sunday": {"start": None, "end": None}  # Closed
}

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Frisor LaFata API is running"}

# User routes
@api_router.post("/auth/register", response_model=dict)
async def register_user(user: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if this is the first user or admin email (make them admin)
    user_count = await db.users.count_documents({})
    admin_emails = ["admin@frisorlafata.dk", "admin2@frisorlafata.dk", "admin3@frisorlafata.dk", "admin4@frisorlafata.dk", "admin6@frisorlafata.dk"]
    
    # Create user
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict.pop('password')
    
    # Debug check
    is_admin = user_count == 0 or user.email in admin_emails
    print(f"User count: {user_count}, Email: {user.email}, Is admin: {is_admin}")
    
    if is_admin:  # First user or admin email becomes admin
        user_dict['is_admin'] = True
    user_obj = User(**user_dict)
    
    # Store user and password separately
    await db.users.insert_one(prepare_for_mongo(user_obj.dict()))
    await db.user_passwords.insert_one({"user_id": user_obj.id, "password": hashed_password})
    
    # Create access token
    access_token = create_access_token(data={"sub": user_obj.id})
    
    return {"access_token": access_token, "token_type": "bearer", "user": user_obj}

@api_router.post("/auth/login", response_model=dict)
async def login_user(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    password_doc = await db.user_passwords.find_one({"user_id": user["id"]})
    if not password_doc or not verify_password(credentials.password, password_doc["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["id"]})
    return {"access_token": access_token, "token_type": "bearer", "user": User(**user)}

@api_router.get("/users/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# User Management routes
@api_router.post("/users", response_model=User)
async def create_user(user_create: UserCreate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_create.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Hash password
    hashed_password = get_password_hash(user_create.password)
    
    user_dict = user_create.dict()
    user_dict.pop('password')
    
    new_user = User(**user_dict)
    await db.users.insert_one(prepare_for_mongo(new_user.dict()))
    await db.user_passwords.insert_one({"user_id": new_user.id, "password": hashed_password})
    
    return new_user

@api_router.get("/users", response_model=List[User])
async def get_all_users(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find().to_list(length=None)
    return [User(**parse_from_mongo(user)) for user in users]

@api_router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user_update: UserUpdate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing_user = await db.users.find_one({"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {}
    for field, value in user_update.dict(exclude_unset=True).items():
        if value is not None:
            if field == "password":
                # Hash new password
                value = get_password_hash(value)
                # Update password in separate collection
                await db.user_passwords.update_one(
                    {"user_id": user_id}, 
                    {"$set": {"password": value}},
                    upsert=True
                )
                continue
            update_data[field] = value
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    updated_user_data = await db.users.find_one({"id": user_id})
    return User(**parse_from_mongo(updated_user_data))

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Prevent deletion of current user
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Also delete password record
    await db.user_passwords.delete_one({"user_id": user_id})
    
    return {"message": "User deleted successfully"}

# Staff routes
@api_router.post("/staff", response_model=Staff)
async def create_staff(staff: StaffCreate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    staff_obj = Staff(**staff.dict())
    await db.staff.insert_one(prepare_for_mongo(staff_obj.dict()))
    return staff_obj

@api_router.get("/staff", response_model=List[Staff])
async def get_staff():
    staff_list = await db.staff.find().to_list(length=None)
    return [Staff(**parse_from_mongo(staff)) for staff in staff_list]

@api_router.put("/staff/{staff_id}", response_model=Staff)
async def update_staff(staff_id: str, staff_update: StaffUpdate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in staff_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.staff.update_one({"id": staff_id}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    updated_staff = await db.staff.find_one({"id": staff_id})
    return Staff(**parse_from_mongo(updated_staff))

@api_router.delete("/staff/{staff_id}")
async def delete_staff(staff_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.staff.delete_one({"id": staff_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    return {"message": "Staff member deleted successfully"}

# Service routes
@api_router.post("/services", response_model=Service)
async def create_service(service: ServiceCreate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service_obj = Service(**service.dict())
    await db.services.insert_one(prepare_for_mongo(service_obj.dict()))
    return service_obj

@api_router.get("/services", response_model=List[Service])
async def get_services():
    services = await db.services.find().to_list(length=None)
    return [Service(**parse_from_mongo(service)) for service in services]

@api_router.put("/services/{service_id}", response_model=Service)
async def update_service(service_id: str, service_update: ServiceUpdate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in service_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.services.update_one({"id": service_id}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    
    updated_service = await db.services.find_one({"id": service_id})
    return Service(**parse_from_mongo(updated_service))

@api_router.delete("/services/{service_id}")
async def delete_service(service_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.services.delete_one({"id": service_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return {"message": "Service deleted successfully"}

async def send_booking_confirmation(booking: Booking):
    """Send booking confirmation email to customer"""
    try:
        # Get settings for email configuration and templates
        settings = await db.settings.find_one({"type": "site_settings"})
        if not settings:
            settings = SiteSettings().dict()
        
        # Check if email is configured
        if not settings.get('email_user') or not settings.get('email_password'):
            print("Email not configured, skipping confirmation email")
            return
        
        # Get staff and services details for the email
        staff = await db.staff.find_one({"id": booking.staff_id})
        services = await db.services.find({"id": {"$in": booking.services}}).to_list(length=None)
        
        # Prepare template variables
        template_vars = {
            'customer_name': booking.customer_name,
            'business_name': settings.get('site_title', 'Frisor LaFata'),
            'booking_date': booking.booking_date.strftime('%d/%m/%Y'),
            'booking_time': booking.booking_time.strftime('%H:%M'),
            'services': ', '.join([service['name'] for service in services]),
            'staff_name': staff.get('name', 'Our team') if staff else 'Our team',
            'total_price': str(booking.total_price),
            'business_address': settings.get('address', ''),
            'business_phone': settings.get('contact_phone', ''),
            'business_email': settings.get('contact_email', '')
        }
        
        # Replace template variables in subject and body
        subject_template = settings.get('email_subject_template', 'Booking Confirmation - {{business_name}}')
        body_template = settings.get('email_body_template', 'Your booking has been confirmed.')
        
        # Simple template replacement
        subject = subject_template
        body = body_template
        
        for var, value in template_vars.items():
            subject = subject.replace(f'{{{{{var}}}}}', str(value))
            body = body.replace(f'{{{{{var}}}}}', str(value))
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = settings.get('email_user')
        msg['To'] = booking.customer_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(settings.get('email_smtp_server', 'smtp.gmail.com'), settings.get('email_smtp_port', 587))
        server.starttls()
        server.login(settings.get('email_user'), settings.get('email_password'))
        
        text = msg.as_string()
        server.sendmail(settings.get('email_user'), booking.customer_email, text)
        server.quit()
        
        print(f"Confirmation email sent to {booking.customer_email}")
        
    except Exception as e:
        print(f"Failed to send confirmation email: {e}")
        # Don't raise the exception - booking should still be created even if email fails

async def send_booking_reminder(booking: Booking):
    """Send booking reminder email 24h before appointment"""
    try:
        # Get settings for email configuration
        settings = await db.settings.find_one({"type": "site_settings"})
        if not settings:
            settings = SiteSettings().dict()
        
        # Check if email is configured and customer has email
        if not settings.get('email_user') or not settings.get('email_password'):
            print("Email not configured, skipping booking reminder")
            return
            
        if not booking.customer_email:
            print("Customer email not available, skipping booking reminder")
            return

        # Get staff and services details for the email
        staff = await db.staff.find_one({"id": booking.staff_id})
        services = await db.services.find({"id": {"$in": booking.services}}).to_list(length=None)
        
        # Prepare template variables
        template_vars = {
            'customer_name': booking.customer_name or 'Valued Customer',
            'business_name': settings.get('site_title', 'Frisor LaFata'),
            'booking_date': booking.booking_date.strftime('%d/%m/%Y'),
            'booking_time': booking.booking_time.strftime('%H:%M'),
            'services': ', '.join([service['name'] for service in services]),
            'staff_name': staff.get('name', 'Our team') if staff else 'Our team',
            'total_price': str(booking.total_price),
            'business_address': settings.get('address', ''),
            'business_phone': settings.get('contact_phone', ''),
            'business_email': settings.get('contact_email', '')
        }
        
        # Reminder email templates
        subject_template = settings.get('reminder_subject_template', 'Appointment Reminder - {{business_name}}')
        body_template = settings.get('reminder_body_template', '''Dear {{customer_name}},

This is a friendly reminder about your upcoming appointment with {{business_name}}.

Appointment Details:
- Date: {{booking_date}}
- Time: {{booking_time}}
- Services: {{services}}
- Staff: {{staff_name}}
- Total Price: {{total_price}} DKK

Location:
{{business_address}}

Phone: {{business_phone}}

Please arrive 5 minutes early. If you need to cancel or reschedule, please contact us as soon as possible.

We look forward to seeing you!

Best regards,
{{business_name}} Team''')
        
        # Replace template variables
        subject = subject_template
        body = body_template
        
        for var, value in template_vars.items():
            subject = subject.replace(f'{{{{{var}}}}}', str(value))
            body = body.replace(f'{{{{{var}}}}}', str(value))
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = settings.get('email_user')
        msg['To'] = booking.customer_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(settings.get('email_smtp_server', 'smtp.gmail.com'), settings.get('email_smtp_port', 587))
        server.starttls()
        server.login(settings.get('email_user'), settings.get('email_password'))
        
        text = msg.as_string()
        server.sendmail(settings.get('email_user'), booking.customer_email, text)
        server.quit()
        
        print(f"Booking reminder sent to {booking.customer_email}")
        
        # Mark reminder as sent
        await db.bookings.update_one(
            {"id": booking.id}, 
            {"$set": {"reminder_sent": True}}
        )
        
    except Exception as e:
        print(f"Failed to send booking reminder: {e}")

@api_router.post("/admin/send-reminders")
async def send_booking_reminders(current_user: User = Depends(get_current_user)):
    """Manual trigger for sending booking reminders"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get bookings for tomorrow (24h from now)
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        tomorrow_date = tomorrow.date()
        
        # Find bookings for tomorrow that haven't had reminders sent
        bookings = await db.bookings.find({
            "booking_date": tomorrow_date.isoformat(),
            "status": {"$in": ["pending", "confirmed"]},
            "reminder_sent": {"$ne": True}
        }).to_list(length=None)
        
        reminders_sent = 0
        for booking_data in bookings:
            booking = Booking(**parse_from_mongo(booking_data))
            await send_booking_reminder(booking)
            reminders_sent += 1
        
        return {"message": f"Sent {reminders_sent} booking reminders"}
        
    except Exception as e:
        print(f"Error sending reminders: {e}")
        raise HTTPException(status_code=500, detail="Failed to send reminders")

# Automatic reminder checking (to be called by a cron job or scheduler)
async def check_and_send_reminders():
    """Check for bookings that need reminders and send them"""
    try:
        # Get bookings for tomorrow (24h from now)
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        tomorrow_date = tomorrow.date()
        
        # Find bookings for tomorrow that haven't had reminders sent
        bookings = await db.bookings.find({
            "booking_date": tomorrow_date.isoformat(),
            "status": {"$in": ["pending", "confirmed"]},
            "reminder_sent": {"$ne": True}
        }).to_list(length=None)
        
        for booking_data in bookings:
            booking = Booking(**parse_from_mongo(booking_data))
            await send_booking_reminder(booking)
        
        print(f"Processed {len(bookings)} booking reminders")
        
    except Exception as e:
        print(f"Error in automatic reminder checking: {e}")

# Existing email function
async def send_booking_email(booking: Booking, email_type: str = "created"):
    """Send booking email based on type (created, confirmed, changed, cancelled)"""
    try:
        # Get settings for email configuration and templates
        settings = await db.settings.find_one({"type": "site_settings"})
        if not settings:
            settings = SiteSettings().dict()
        
        # Check if email is configured and customer has email
        if not settings.get('email_user') or not settings.get('email_password'):
            print("Email not configured, skipping booking email")
            return
            
        if not booking.customer_email:
            print("Customer email not available, skipping booking email")
            return
        
        # Get staff and services details for the email
        staff = await db.staff.find_one({"id": booking.staff_id})
        services = await db.services.find({"id": {"$in": booking.services}}).to_list(length=None)
        
        # Prepare template variables
        template_vars = {
            'customer_name': booking.customer_name or 'Valued Customer',
            'business_name': settings.get('site_title', 'Frisor LaFata'),
            'booking_date': booking.booking_date.strftime('%d/%m/%Y'),
            'booking_time': booking.booking_time.strftime('%H:%M'),
            'services': ', '.join([service['name'] for service in services]),
            'staff_name': staff.get('name', 'Our team') if staff else 'Our team',
            'total_price': str(booking.total_price),
            'business_address': settings.get('address', ''),
            'business_phone': settings.get('contact_phone', ''),
            'business_email': settings.get('contact_email', ''),
            'admin_notes': getattr(booking, 'admin_notes', '')
        }
        
        # Select template based on email type
        if email_type == "created":
            subject_template = settings.get('email_subject_template', 'Booking Confirmation - {{business_name}}')
            body_template = settings.get('email_body_template', 'Your booking has been created.')
        elif email_type == "confirmed":
            subject_template = settings.get('email_confirmation_subject', 'Booking Confirmed - {{business_name}}')
            body_template = settings.get('email_confirmation_body', 'Your booking has been confirmed.')
        elif email_type == "changed":
            subject_template = settings.get('email_change_subject', 'Booking Changed - {{business_name}}')
            body_template = settings.get('email_change_body', 'Your booking has been changed.')
        else:
            # Default to created
            subject_template = settings.get('email_subject_template', 'Booking Confirmation - {{business_name}}')
            body_template = settings.get('email_body_template', 'Your booking has been created.')
        
        # Replace template variables in subject and body
        subject = subject_template
        body = body_template
        
        for var, value in template_vars.items():
            subject = subject.replace(f'{{{{{var}}}}}', str(value))
            body = body.replace(f'{{{{{var}}}}}', str(value))
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = settings.get('email_user')
        msg['To'] = booking.customer_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(settings.get('email_smtp_server', 'smtp.gmail.com'), settings.get('email_smtp_port', 587))
        server.starttls()
        server.login(settings.get('email_user'), settings.get('email_password'))
        
        text = msg.as_string()
        server.sendmail(settings.get('email_user'), booking.customer_email, text)
        server.quit()
        
        print(f"Booking email ({email_type}) sent to {booking.customer_email}")
        
    except Exception as e:
        print(f"Failed to send booking email: {e}")
        # Don't raise the exception - booking should still be created even if email fails

# Booking routes
@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking: BookingCreate):
    # Calculate total duration and price
    services = await db.services.find({"id": {"$in": booking.services}}).to_list(length=None)
    if len(services) != len(booking.services):
        raise HTTPException(status_code=400, detail="One or more services not found")
    
    total_duration = sum(service["duration_minutes"] for service in services)
    total_price = sum(service["price"] for service in services)
    
    # Enhanced conflict checking - prevent double booking
    booking_start_time = datetime.combine(booking.booking_date, booking.booking_time)
    booking_end_time = booking_start_time + timedelta(minutes=total_duration)
    
    # Find overlapping bookings for the same staff
    existing_bookings = await db.bookings.find({
        "staff_id": booking.staff_id,
        "booking_date": booking.booking_date.isoformat(),
        "status": {"$in": ["pending", "confirmed"]}  # Only check active bookings
    }).to_list(length=None)
    
    for existing in existing_bookings:
        existing_start = datetime.combine(
            booking.booking_date, 
            datetime.strptime(existing["booking_time"], '%H:%M:%S').time()
        )
        existing_end = existing_start + timedelta(minutes=existing["total_duration"])
        
        # Check for overlap
        if (booking_start_time < existing_end and booking_end_time > existing_start):
            raise HTTPException(
                status_code=400, 
                detail=f"Time slot conflicts with existing booking at {existing['booking_time']}"
            )
    
    booking_dict = booking.dict()
    booking_dict.update({
        "total_duration": total_duration,
        "total_price": total_price,
        "status": "pending",  # New bookings start as pending
        "updated_at": datetime.now(timezone.utc)
    })
    
    booking_obj = Booking(**booking_dict)
    await db.bookings.insert_one(prepare_for_mongo(booking_obj.dict()))
    
    # Send initial booking email (pending confirmation)
    await send_booking_email(booking_obj, "created")
    
    return booking_obj

@api_router.get("/bookings", response_model=List[Booking])
async def get_bookings(current_user: User = Depends(get_current_user)):
    if current_user.is_admin:
        bookings = await db.bookings.find().to_list(length=None)
    else:
        bookings = await db.bookings.find({"customer_id": current_user.id}).to_list(length=None)
    
    return [Booking(**parse_from_mongo(booking)) for booking in bookings]

@api_router.put("/bookings/{booking_id}", response_model=Booking)
async def update_booking(booking_id: str, booking_update: BookingUpdate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing_booking = await db.bookings.find_one({"id": booking_id})
    if not existing_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Track if we're changing the time/date for email notification
    time_changed = False
    original_date = existing_booking.get("booking_date")
    original_time = existing_booking.get("booking_time")
    
    update_data = {}
    for field, value in booking_update.dict(exclude_unset=True).items():
        if value is not None:
            if field in ["booking_date", "booking_time"]:
                # Check for time/date changes
                if field == "booking_date" and value.isoformat() != original_date:
                    time_changed = True
                elif field == "booking_time" and value.strftime('%H:%M:%S') != original_time:
                    time_changed = True
                    
            update_data[field] = prepare_for_mongo({field: value})[field]
    
    # If changing time/date, check for conflicts
    if "booking_date" in update_data or "booking_time" in update_data:
        new_date = datetime.fromisoformat(update_data.get("booking_date", original_date)).date()
        new_time_str = update_data.get("booking_time", original_time)
        if isinstance(new_time_str, str):
            new_time = datetime.strptime(new_time_str, '%H:%M:%S').time()
        else:
            new_time = new_time_str
            
        # Enhanced conflict checking for rescheduling
        booking_start_time = datetime.combine(new_date, new_time)
        booking_end_time = booking_start_time + timedelta(minutes=existing_booking["total_duration"])
        
        # Find overlapping bookings (excluding current booking)
        existing_bookings = await db.bookings.find({
            "staff_id": existing_booking["staff_id"],
            "booking_date": new_date.isoformat(),
            "status": {"$in": ["pending", "confirmed"]},
            "id": {"$ne": booking_id}  # Exclude current booking
        }).to_list(length=None)
        
        for existing in existing_bookings:
            existing_start = datetime.combine(
                new_date, 
                datetime.strptime(existing["booking_time"], '%H:%M:%S').time()
            )
            existing_end = existing_start + timedelta(minutes=existing["total_duration"])
            
            # Check for overlap
            if (booking_start_time < existing_end and booking_end_time > existing_start):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Time slot conflicts with existing booking at {existing['booking_time']}"
                )
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.bookings.update_one({"id": booking_id}, {"$set": update_data})
    
    # Get updated booking
    updated_booking_data = await db.bookings.find_one({"id": booking_id})
    updated_booking = Booking(**parse_from_mongo(updated_booking_data))
    
    # Send appropriate email notification
    if time_changed:
        await send_booking_email(updated_booking, "changed")
    elif booking_update.status == "confirmed":
        await send_booking_email(updated_booking, "confirmed")
    
    return updated_booking

@api_router.put("/bookings/{booking_id}/confirm")
async def confirm_booking(booking_id: str, current_user: User = Depends(get_current_user)):
    """Confirm a pending booking"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing_booking = await db.bookings.find_one({"id": booking_id})
    if not existing_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    await db.bookings.update_one(
        {"id": booking_id}, 
        {"$set": {"status": "confirmed", "updated_at": datetime.now(timezone.utc)}}
    )
    
    # Get updated booking and send confirmation email
    updated_booking_data = await db.bookings.find_one({"id": booking_id})
    updated_booking = Booking(**parse_from_mongo(updated_booking_data))
    
    await send_booking_email(updated_booking, "confirmed")
    
    return {"message": "Booking confirmed successfully"}

@api_router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.bookings.delete_one({"id": booking_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {"message": "Booking deleted successfully"}

@api_router.get("/bookings/available-slots")
async def get_available_slots(staff_id: str, date_param: str):
    """Get available time slots for a specific staff member and date"""
    booking_date = datetime.fromisoformat(date_param).date()
    day_name = booking_date.strftime('%A').lower()
    
    # Check if staff works on this day
    staff_member = await db.staff.find_one({"id": staff_id})
    if not staff_member:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    # Get staff available hours or use business hours
    staff_hours = staff_member.get("available_hours", {}).get(day_name)
    if staff_hours and staff_hours.get("enabled", False):
        business_hours = {"start": staff_hours["start"], "end": staff_hours["end"]}
    else:
        business_hours = BUSINESS_HOURS.get(day_name)
    
    if not business_hours or not business_hours["start"]:
        return {"available_slots": []}
    
    # Get existing bookings for this date and staff
    existing_bookings = await db.bookings.find({
        "staff_id": staff_id,
        "booking_date": booking_date.isoformat(),
        "status": {"$ne": "cancelled"}
    }).to_list(length=None)
    
    # Generate time slots (30-minute intervals)
    from datetime import timedelta
    start_time = datetime.strptime(business_hours["start"], "%H:%M").time()
    end_time = datetime.strptime(business_hours["end"], "%H:%M").time()
    
    slots = []
    current = datetime.combine(booking_date, start_time)
    end_datetime = datetime.combine(booking_date, end_time)
    
    while current < end_datetime:
        slot_time = current.time()
        is_available = True
        
        # Check if slot conflicts with existing bookings
        for booking in existing_bookings:
            booking_time = datetime.strptime(booking["booking_time"], "%H:%M:%S").time()
            booking_end = (datetime.combine(booking_date, booking_time) + 
                          timedelta(minutes=booking["total_duration"])).time()
            
            if (slot_time >= booking_time and slot_time < booking_end):
                is_available = False
                break
        
        if is_available:
            slots.append(slot_time.strftime("%H:%M"))
        
        current += timedelta(minutes=30)
    
    return {"available_slots": slots}

# Corporate Booking routes
@api_router.post("/corporate-bookings", response_model=CorporateBooking)
async def create_corporate_booking(booking: CorporateBookingCreate):
    try:
        # Calculate total services price
        all_service_ids = []
        for employee in booking.employees:
            all_service_ids.extend(employee.service_ids)
        
        services = await db.services.find({"id": {"$in": all_service_ids}}).to_list(length=None)
        total_services_price = sum(service['price'] for service in services)
        
        # Calculate total duration (for scheduling purposes)
        total_duration = sum(service['duration_minutes'] for service in services)
        
        # Create corporate booking object
        booking_data = booking.dict()
        booking_data.update({
            "id": str(uuid.uuid4()),
            "total_employees": len(booking.employees),
            "total_services_price": total_services_price,
            "total_price": total_services_price + booking.company_travel_fee,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        corporate_booking = CorporateBooking(**booking_data)
        
        # Convert to dict for MongoDB
        booking_dict = corporate_booking.dict()
        if isinstance(booking_dict.get('booking_date'), date):
            booking_dict['booking_date'] = booking_dict['booking_date'].isoformat()
        if isinstance(booking_dict.get('booking_time'), time):
            booking_dict['booking_time'] = booking_dict['booking_time'].strftime('%H:%M:%S')
        
        # Insert into database
        await db.corporate_bookings.insert_one(booking_dict)
        
        # Send confirmation email to company
        try:
            await send_corporate_booking_confirmation_email(corporate_booking, services)
        except Exception as e:
            print(f"Failed to send corporate booking confirmation email: {e}")
        
        return corporate_booking
    except Exception as e:
        print(f"Error creating corporate booking: {e}")
        raise HTTPException(status_code=500, detail="Error creating corporate booking")

@api_router.get("/corporate-bookings", response_model=List[CorporateBooking])
async def get_corporate_bookings(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        bookings = await db.corporate_bookings.find().to_list(length=None)
        
        # Convert date/time strings back to proper types
        for booking in bookings:
            if isinstance(booking.get('booking_date'), str):
                booking['booking_date'] = datetime.fromisoformat(booking['booking_date']).date()
            if isinstance(booking.get('booking_time'), str):
                booking['booking_time'] = datetime.strptime(booking['booking_time'], '%H:%M:%S').time()
        
        return bookings
    except Exception as e:
        print(f"Error getting corporate bookings: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving corporate bookings")

@api_router.get("/corporate-bookings/{booking_id}", response_model=CorporateBooking)
async def get_corporate_booking(booking_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    booking = await db.corporate_bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Corporate booking not found")
    
    # Convert date/time strings back to proper types
    if isinstance(booking.get('booking_date'), str):
        booking['booking_date'] = datetime.fromisoformat(booking['booking_date']).date()
    if isinstance(booking.get('booking_time'), str):
        booking['booking_time'] = datetime.strptime(booking['booking_time'], '%H:%M:%S').time()
    
    return booking

@api_router.put("/corporate-bookings/{booking_id}", response_model=CorporateBooking)
async def update_corporate_booking(
    booking_id: str, 
    booking_update: CorporateBookingUpdate, 
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Prepare update data
    update_data = {k: v for k, v in booking_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    # Convert date/time objects to strings for MongoDB
    if 'booking_date' in update_data and isinstance(update_data['booking_date'], date):
        update_data['booking_date'] = update_data['booking_date'].isoformat()
    if 'booking_time' in update_data and isinstance(update_data['booking_time'], time):
        update_data['booking_time'] = update_data['booking_time'].strftime('%H:%M:%S')
    
    result = await db.corporate_bookings.update_one(
        {"id": booking_id}, 
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Corporate booking not found")
    
    # Return updated booking
    updated_booking = await db.corporate_bookings.find_one({"id": booking_id})
    
    # Convert date/time strings back to proper types
    if isinstance(updated_booking.get('booking_date'), str):
        updated_booking['booking_date'] = datetime.fromisoformat(updated_booking['booking_date']).date()
    if isinstance(updated_booking.get('booking_time'), str):
        updated_booking['booking_time'] = datetime.strptime(updated_booking['booking_time'], '%H:%M:%S').time()
    
    return updated_booking

@api_router.delete("/corporate-bookings/{booking_id}")
async def delete_corporate_booking(booking_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.corporate_bookings.delete_one({"id": booking_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Corporate booking not found")
    
    return {"message": "Corporate booking deleted successfully"}

# Helper function for corporate booking confirmation email
async def send_corporate_booking_confirmation_email(booking: CorporateBooking, services: list):
    """Send confirmation email for corporate booking"""
    try:
        # Get staff info
        staff = await db.staff.find_one({"id": booking.staff_id})
        staff_name = staff['name'] if staff else "Unknown Staff"
        
        # Create services summary
        services_summary = []
        for employee in booking.employees:
            employee_services = []
            for service_id in employee.service_ids:
                service = next((s for s in services if s['id'] == service_id), None)
                if service:
                    employee_services.append(f"{service['name']} ({service['duration_minutes']} min, {service['price']} DKK)")
            services_summary.append(f"{employee.employee_name}: {', '.join(employee_services)}")
        
        # Email content
        subject = f"Corporate Booking Confirmation - {booking.company_name}"
        body = f"""
Kære {booking.company_contact_person},

Tak for din corporate booking hos Frisor LaFata!

FIRMA DETALJER:
- Firma: {booking.company_name}
- Kontaktperson: {booking.company_contact_person}
- E-mail: {booking.company_email}
- Telefon: {booking.company_phone}
- Adresse: {booking.company_address}, {booking.company_city} {booking.company_postal_code}

BOOKING DETALJER:
- Dato: {booking.booking_date}
- Tid: {booking.booking_time}
- Frisør: {staff_name}
- Antal medarbejdere: {booking.total_employees}

SERVICES PR. MEDARBEJDER:
{chr(10).join(services_summary)}

PRISER:
- Services total: {booking.total_services_price} DKK
- Rejseomkostninger: {booking.company_travel_fee} DKK
- Total pris: {booking.total_price} DKK

{f'Særlige krav: {booking.special_requirements}' if booking.special_requirements else ''}

Vi glæder os til at komme ud til jer!

Med venlig hilsen,
Frisor LaFata
"""
        
        # Send email (using existing email infrastructure)
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # This would use the existing email configuration
        print(f"Corporate booking confirmation email prepared for {booking.company_email}")
        # Note: Actual email sending would use the existing email infrastructure from the app
        
    except Exception as e:
        print(f"Error sending corporate booking confirmation email: {e}")
        raise e

# File upload routes
@api_router.post("/upload/avatar")
async def upload_avatar(avatar: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate file type
    if not avatar.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/avatars")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = avatar.filename.split('.')[-1] if '.' in avatar.filename else 'jpg'
    filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = upload_dir / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await avatar.read()
        buffer.write(content)
    
    # Return full URL for the image
    avatar_url = f"{BACKEND_URL}/api/uploads/avatars/{filename}"
    return {"avatar_url": avatar_url}

@api_router.post("/upload/video")
async def upload_video(video: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate file type
    allowed_video_types = ['video/mp4', 'video/webm', 'video/ogg', 'video/avi', 'video/mov']
    if video.content_type not in allowed_video_types:
        raise HTTPException(status_code=400, detail="File must be a supported video format (mp4, webm, ogg, avi, mov)")
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/videos")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = video.filename.split('.')[-1] if '.' in video.filename else 'mp4'
    filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = upload_dir / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await video.read()
        buffer.write(content)
    
    # Return full URL for the video
    video_url = f"{BACKEND_URL}/api/uploads/videos/{filename}"
    return {"video_url": video_url}

@api_router.post("/upload/image")
async def upload_image(image: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate file type
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/images")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = image.filename.split('.')[-1] if '.' in image.filename else 'jpg'
    filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = upload_dir / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await image.read()
        buffer.write(content)
    
    # Return full URL for the image
    image_url = f"{BACKEND_URL}/api/uploads/images/{filename}"
    return {"image_url": image_url}

@api_router.get("/uploads/{file_type}/{filename}")
async def serve_uploaded_file(file_type: str, filename: str):
    """Serve uploaded files with correct content-type headers"""
    allowed_types = ["avatars", "images", "videos"]
    if file_type not in allowed_types:
        raise HTTPException(status_code=404, detail="File type not found")
    
    file_path = f"uploads/{file_type}/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine the correct MIME type
    content_type, _ = mimetypes.guess_type(file_path)
    if content_type is None:
        # Default content types based on file extension
        if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            content_type = "image/jpeg"
        elif filename.lower().endswith('.png'):
            content_type = "image/png"
        elif filename.lower().endswith('.gif'):
            content_type = "image/gif"
        elif filename.lower().endswith('.webp'):
            content_type = "image/webp"
        elif filename.lower().endswith('.mp4'):
            content_type = "video/mp4"
        elif filename.lower().endswith('.webm'):
            content_type = "video/webm"
        elif filename.lower().endswith('.ogg'):
            content_type = "video/ogg"
        else:
            content_type = "application/octet-stream"
    
    return FileResponse(
        file_path, 
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=3600"}
    )

# Page routes
@api_router.post("/pages", response_model=Page)
async def create_page(page: PageCreate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if slug already exists
    existing_page = await db.pages.find_one({"slug": page.slug})
    if existing_page:
        raise HTTPException(status_code=400, detail="Page with this slug already exists")
    
    page_obj = Page(**page.dict())
    await db.pages.insert_one(prepare_for_mongo(page_obj.dict()))
    return page_obj

@api_router.get("/pages", response_model=List[Page])
async def get_pages(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    pages = await db.pages.find().to_list(length=None)
    return [Page(**parse_from_mongo(page)) for page in pages]

@api_router.get("/public/pages", response_model=List[Page])
async def get_public_pages():
    """Get published pages for public navigation"""
    pages = await db.pages.find({
        "is_published": True,
        "show_in_navigation": True
    }).sort("navigation_order", 1).to_list(length=None)
    return [Page(**parse_from_mongo(page)) for page in pages]

@api_router.get("/pages/{slug}", response_model=Page)
async def get_page_by_slug(slug: str):
    page = await db.pages.find_one({"slug": slug, "is_published": True})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return Page(**parse_from_mongo(page))

@api_router.put("/pages/{page_id}", response_model=Page)
async def update_page(page_id: str, page_update: PageUpdate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in page_update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.pages.update_one({"id": page_id}, {"$set": update_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Page not found")
    
    updated_page = await db.pages.find_one({"id": page_id})
    return Page(**parse_from_mongo(updated_page))

@api_router.delete("/pages/{page_id}")
async def delete_page(page_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.pages.delete_one({"id": page_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Page not found")
    
    return {"message": "Page deleted successfully"}

# Settings routes
@api_router.get("/settings")
async def get_settings(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = await db.settings.find_one({"type": "site_settings"})
    if not settings:
        # Return default settings
        default_settings = SiteSettings()
        return default_settings.dict()
    
    # Remove MongoDB _id and type fields
    settings.pop("_id", None)
    settings.pop("type", None)
    return settings

@api_router.put("/settings")
async def update_settings(settings: Dict[str, Any], current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings_data = {
        "type": "site_settings",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **settings
    }
    
    await db.settings.update_one(
        {"type": "site_settings"},
        {"$set": settings_data},
        upsert=True
    )
    
    return {"message": "Settings updated successfully"}

# Public settings endpoint for frontend
@api_router.get("/public/settings")
async def get_public_settings():
    """Get public site settings (excludes sensitive data like API keys)"""
    try:
        # Use MongoDB instead of MySQL until MySQL is properly configured
        settings = await db.settings.find_one({"type": "site_settings"})
        
        if not settings:
            # Return default public settings
            return {
                "site_title": "Frisor LaFata",
                "site_description": "Klassisk barbering siden 2010",
                "contact_phone": "+45 12 34 56 78",
                "contact_email": "info@frisorlafata.dk",
                "address": "Hovedgaden 123, 1000 København",
                "hero_title": "Klassisk Barbering",
                "hero_subtitle": "i Hjertet af Byen",
                "hero_description": "Oplev den autentiske barber-oplevelse hos Frisor LaFata.",
                "hero_image": "",
                "hero_image_opacity": 30,  # Default 30% opacity
                # Social Media Settings
                "social_media_enabled": True,
                "social_media_title": "Follow Us",
                "social_media_description": "Se vores seneste arbejde og tilbud på sociale medier",
                # Instagram
                "instagram_enabled": True,
                "instagram_username": "",
                "instagram_hashtag": "",
                "instagram_embed_code": "",
                # Facebook
                "facebook_enabled": True,
                "facebook_page_url": "",
                "facebook_embed_code": "",
                # TikTok
                "tiktok_enabled": False,
                "tiktok_username": "",
                "tiktok_embed_code": "",
                # Twitter/X
                "twitter_enabled": False,
                "twitter_username": "",
                "twitter_embed_code": "",
                # YouTube
                "youtube_enabled": False,
                "youtube_channel_url": "",
                "youtube_embed_code": "",
                # Booking System Settings
                "booking_system_enabled": True,
                "home_service_enabled": True,
                "home_service_fee": 150.00,
                "home_service_description": "Vi kommer til dig! Oplev professionel barbering i dit eget hjem."
            }
        
        # Remove MongoDB _id and sensitive fields, return only public settings
        settings.pop("_id", None)
        settings.pop("type", None)
        settings.pop("paypal_client_id", None)
        settings.pop("paypal_client_secret", None) 
        settings.pop("email_user", None)
        settings.pop("email_password", None)
        
        return settings
        
    except Exception as e:
        print(f"Error getting public settings: {e}")
        # Return default settings if error occurs
        return {
            "site_title": "Frisor LaFata",
            "site_description": "Klassisk barbering siden 2010",
            "contact_phone": "+45 12 34 56 78",
            "contact_email": "info@frisorlafata.dk",
            "address": "Hovedgaden 123, 1000 København",
            "hero_title": "Klassisk Barbering",
            "hero_subtitle": "i Hjertet af Byen",
            "hero_description": "Oplev den autentiske barber-oplevelse hos Frisor LaFata.",
            "hero_image": "",
            "hero_image_opacity": 30,  # Default 30% opacity
            "social_media_enabled": True,
            "social_media_title": "Follow Us",
            "social_media_description": "Se vores seneste arbejde og tilbud på sociale medier",
            "instagram_enabled": True,
            "facebook_enabled": True,
            "tiktok_enabled": False,
            "twitter_enabled": False,
            "youtube_enabled": False,
            "booking_system_enabled": True,
            "home_service_enabled": True,
            "home_service_fee": 150.00,
            "home_service_description": "Vi kommer til dig! Oplev professionel barbering i dit eget hjem."
        }

# Homepage Layout Management
@api_router.get("/homepage/sections")
async def get_homepage_sections(current_user: User = Depends(get_current_user)):
    """Get all homepage sections for admin editing"""
    try:
        # Use MongoDB for now until MySQL is properly configured
        sections = await db.homepage_sections.find().sort("section_order", 1).to_list(length=None)
        
        # Remove MongoDB _id field from each section
        for section in sections:
            section.pop("_id", None)
        
        # If no sections exist, create default sections
        if not sections:
            default_sections = [
                {
                    "id": "hero-section",
                    "section_type": "hero",
                    "section_order": 1,
                    "is_enabled": True,
                    "title": "Klassisk Barbering",
                    "subtitle": "i Hjertet af Byen", 
                    "description": "Oplev den autentiske barber-oplevelse hos Frisor LaFata.",
                    "button_text": "Book din tid nu",
                    "button_action": "open_booking",
                    "background_color": "#000000",
                    "text_color": "#D4AF37"
                },
                {
                    "id": "services-section",
                    "section_type": "services",
                    "section_order": 2,
                    "is_enabled": True,
                    "title": "Vores Services",
                    "subtitle": "Professionel barbering og styling",
                    "description": "Vi tilbyder et bredt udvalg af tjenester fra klassiske klipninger til moderne styling.",
                    "button_text": "",
                    "button_action": "none",
                    "background_color": "#000000",
                    "text_color": "#D4AF37"
                },
                {
                    "id": "staff-section",
                    "section_type": "staff",
                    "section_order": 3,
                    "is_enabled": True,
                    "title": "Mød Vores Team",
                    "subtitle": "Erfarne barbere med passion",
                    "description": "Vores dygtige barbere har mange års erfaring og står klar til at give dig den perfekte look.",
                    "button_text": "",
                    "button_action": "none",
                    "background_color": "#000000",
                    "text_color": "#D4AF37"
                },
                {
                    "id": "gallery-section",
                    "section_type": "gallery",
                    "section_order": 4,
                    "is_enabled": True,
                    "title": "Galleri",
                    "subtitle": "Se vores arbejde",
                    "description": "Få inspiration fra vores før og efter billeder.",
                    "button_text": "",
                    "button_action": "none",
                    "background_color": "#000000",
                    "text_color": "#D4AF37"
                },
                {
                    "id": "social-section",
                    "section_type": "social",
                    "section_order": 5,
                    "is_enabled": True,
                    "title": "Følg Os",
                    "subtitle": "Se vores seneste arbejde",
                    "description": "Hold dig opdateret med vores seneste trends og tilbud på sociale medier.",
                    "button_text": "",
                    "button_action": "none",
                    "background_color": "#000000",
                    "text_color": "#D4AF37"
                },
                {
                    "id": "contact-section",
                    "section_type": "contact",
                    "section_order": 6,
                    "is_enabled": True,
                    "title": "Kontakt Os",
                    "subtitle": "Book din tid i dag",
                    "description": "Kontakt os for at booke din næste barbering eller hvis du har spørgsmål.",
                    "button_text": "Gå til booking system",
                    "button_action": "open_booking",
                    "background_color": "#000000",
                    "text_color": "#D4AF37"
                }
            ]
            
            # Insert default sections
            for section in default_sections:
                await db.homepage_sections.insert_one(section)
            
            sections = default_sections
        
        return sections
    except Exception as e:
        print(f"Error getting homepage sections: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving homepage sections")

@api_router.get("/public/homepage/sections")
async def get_public_homepage_sections():
    """Get enabled homepage sections for public display"""
    try:
        sections = await db.homepage_sections.find({"is_enabled": True}).sort("section_order", 1).to_list(length=None)
        
        # Remove MongoDB _id field from each section
        for section in sections:
            section.pop("_id", None)
            
        return sections
    except Exception as e:
        print(f"Error getting public homepage sections: {e}")
        # Return default sections if database error
        return [
            {
                "id": "hero-section",
                "section_type": "hero",
                "section_order": 1,
                "is_enabled": True,
                "title": "Klassisk Barbering",
                "subtitle": "i Hjertet af Byen",
                "description": "Oplev den autentiske barber-oplevelse hos Frisor LaFata.",
                "button_text": "Book din tid nu",
                "button_action": "open_booking"
            }
        ]

class HomepageSectionReorder(BaseModel):
    sections: List[dict]

@api_router.put("/homepage/sections/reorder")
async def reorder_homepage_sections(reorder_data: HomepageSectionReorder, current_user: User = Depends(get_current_user)):
    """Reorder homepage sections"""
    try:
        for section in reorder_data.sections:
            result = await db.homepage_sections.update_one(
                {"id": section['id']},
                {"$set": {"section_order": section['section_order']}}
            )
            if result.matched_count == 0:
                print(f"Warning: Section with id '{section['id']}' not found")
        return {"message": "Sections reordered successfully"}
    except Exception as e:
        print(f"Error reordering homepage sections: {e}")
        raise HTTPException(status_code=500, detail=f"Error reordering homepage sections: {str(e)}")

@api_router.put("/homepage/sections/{section_id}")
async def update_homepage_section(section_id: str, section_data: dict, current_user: User = Depends(get_current_user)):
    """Update a homepage section"""
    try:
        result = await db.homepage_sections.update_one(
            {"id": section_id}, 
            {"$set": section_data}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Section not found")
        return {"message": "Section updated successfully"}
    except Exception as e:
        print(f"Error updating homepage section: {e}")
        raise HTTPException(status_code=500, detail="Error updating homepage section")

@api_router.post("/payments/paypal/create")
async def create_paypal_payment(booking_id: str, amount: float = None):
    """Create PayPal payment for a booking"""
    try:
        # Get booking details if amount not provided
        if not amount:
            booking = await db.bookings.find_one({"id": booking_id})
            if not booking:
                raise HTTPException(status_code=404, detail="Booking not found")
            amount = booking["total_price"]
        
        # Create PayPal payment
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": f"https://barber-fullstack-fix.preview.emergentagent.com/payment/success?booking_id={booking_id}",
                "cancel_url": f"https://barber-fullstack-fix.preview.emergentagent.com/payment/cancel?booking_id={booking_id}"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "Barbershop Services - Frisor LaFata",
                        "sku": booking_id,
                        "price": str(amount),
                        "currency": "DKK",
                        "quantity": 1
                    }]
                },
                "amount": {"total": str(amount), "currency": "DKK"},
                "description": f"Booking #{booking_id} - Frisor LaFata"
            }]
        })
        
        if payment.create():
            # Find approval URL
            approval_url = None
            for link in payment.links:
                if link.rel == "approval_url":
                    approval_url = link.href
                    break
            
            # Store payment info
            await db.payments.insert_one({
                "booking_id": booking_id,
                "paypal_payment_id": payment.id,
                "amount": amount,
                "currency": "DKK",
                "status": "created",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            
            return {
                "payment_id": payment.id,
                "approval_url": approval_url,
                "status": "created",
                "sandbox_mode": PAYPAL_CONFIG["sandbox_mode"]
            }
        else:
            raise HTTPException(status_code=400, detail=f"PayPal error: {payment.error}")
            
    except Exception as e:
        logging.error(f"PayPal payment creation failed: {e}")
        return {
            "payment_id": f"SANDBOX_{booking_id}",
            "approval_url": f"https://www.sandbox.paypal.com/checkoutnow?token=sandbox_demo",
            "status": "sandbox_demo",
            "sandbox_mode": PAYPAL_CONFIG["sandbox_mode"],
            "error": "Using demo mode - PayPal not configured"
        }

@api_router.post("/payments/paypal/execute")
async def execute_paypal_payment(payment_id: str, payer_id: str):
    """Execute PayPal payment after user approval"""
    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            # Update payment status
            await db.payments.update_one(
                {"paypal_payment_id": payment_id},
                {"$set": {
                    "status": "completed",
                    "payer_id": payer_id,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Update booking payment status
            payment_doc = await db.payments.find_one({"paypal_payment_id": payment_id})
            if payment_doc:
                await db.bookings.update_one(
                    {"id": payment_doc["booking_id"]},
                    {"$set": {"payment_status": "paid"}}
                )
            
            return {"status": "success", "payment_id": payment_id}
        else:
            raise HTTPException(status_code=400, detail=f"PayPal execution error: {payment.error}")
            
    except Exception as e:
        logging.error(f"PayPal payment execution failed: {e}")
        raise HTTPException(status_code=500, detail="Payment execution failed")

# Email template routes
@api_router.post("/email-templates", response_model=EmailTemplate)
async def create_email_template(template: EmailTemplateCreate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    template_obj = EmailTemplate(**template.dict())
    await db.email_templates.insert_one(prepare_for_mongo(template_obj.dict()))
    return template_obj

@api_router.get("/email-templates", response_model=List[EmailTemplate])
async def get_email_templates(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    templates = await db.email_templates.find().to_list(length=None)
    return [EmailTemplate(**parse_from_mongo(template)) for template in templates]

# Gallery routes
@api_router.post("/gallery", response_model=GalleryItem)
async def create_gallery_item(gallery_item: GalleryItemCreate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    new_gallery_item = GalleryItem(**gallery_item.dict())
    await db.gallery.insert_one(prepare_for_mongo(new_gallery_item.dict()))
    
    return new_gallery_item

@api_router.get("/gallery", response_model=List[GalleryItem])
async def get_gallery_items(featured_only: bool = False):
    """Get gallery items - public endpoint"""
    query = {"is_featured": True} if featured_only else {}
    gallery_items = await db.gallery.find(query).sort("created_at", -1).to_list(length=None)
    return [GalleryItem(**parse_from_mongo(item)) for item in gallery_items]

@api_router.get("/admin/gallery", response_model=List[GalleryItem])
async def get_all_gallery_items(current_user: User = Depends(get_current_user)):
    """Get all gallery items - admin only"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    gallery_items = await db.gallery.find().sort("created_at", -1).to_list(length=None)
    return [GalleryItem(**parse_from_mongo(item)) for item in gallery_items]

@api_router.put("/gallery/{item_id}", response_model=GalleryItem)
async def update_gallery_item(item_id: str, gallery_update: GalleryItemUpdate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing_item = await db.gallery.find_one({"id": item_id})
    if not existing_item:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    
    update_data = {}
    for field, value in gallery_update.dict(exclude_unset=True).items():
        if value is not None:
            update_data[field] = value
    
    if update_data:
        await db.gallery.update_one({"id": item_id}, {"$set": update_data})
    
    updated_item_data = await db.gallery.find_one({"id": item_id})
    return GalleryItem(**parse_from_mongo(updated_item_data))

@api_router.delete("/gallery/{item_id}")
async def delete_gallery_item(item_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.gallery.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Gallery item not found")
    
    return {"message": "Gallery item deleted successfully"}

# Staff break management routes
@api_router.post("/staff-breaks", response_model=StaffBreak)
async def create_staff_break(break_data: StaffBreakCreate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate that staff member exists
    staff = await db.staff.find_one({"id": break_data.staff_id})
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    new_break = StaffBreak(**break_data.dict(), created_by=current_user.id)
    await db.staff_breaks.insert_one(prepare_for_mongo(new_break.dict()))
    
    return new_break

@api_router.get("/staff-breaks", response_model=List[StaffBreak])
async def get_staff_breaks(
    staff_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get staff breaks with optional filtering"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = {}
    if staff_id:
        query["staff_id"] = staff_id
    
    if start_date and end_date:
        query["$or"] = [
            {
                "start_date": {"$lte": end_date},
                "end_date": {"$gte": start_date}
            }
        ]
    
    breaks = await db.staff_breaks.find(query).sort("start_date", 1).to_list(length=None)
    return [StaffBreak(**parse_from_mongo(break_item)) for break_item in breaks]

@api_router.get("/staff-breaks/availability/{staff_id}")
async def check_staff_availability(
    staff_id: str,
    check_date: str,
    start_time: str,
    end_time: str
):
    """Check if staff member is available at a specific time"""
    try:
        check_date_obj = datetime.fromisoformat(check_date).date()
        start_time_obj = datetime.strptime(start_time, '%H:%M:%S').time()
        end_time_obj = datetime.strptime(end_time, '%H:%M:%S').time()
        
        # Find overlapping breaks
        breaks = await db.staff_breaks.find({
            "staff_id": staff_id,
            "start_date": {"$lte": check_date_obj.isoformat()},
            "end_date": {"$gte": check_date_obj.isoformat()}
        }).to_list(length=None)
        
        conflicts = []
        for break_item in breaks:
            break_start = datetime.strptime(break_item["start_time"], '%H:%M:%S').time()
            break_end = datetime.strptime(break_item["end_time"], '%H:%M:%S').time()
            
            # Check for time overlap
            if (start_time_obj < break_end and end_time_obj > break_start):
                conflicts.append({
                    "break_id": break_item["id"],
                    "break_type": break_item["break_type"],
                    "reason": break_item["reason"],
                    "start_time": break_item["start_time"],
                    "end_time": break_item["end_time"]
                })
        
        return {
            "is_available": len(conflicts) == 0,
            "conflicts": conflicts
        }
        
    except Exception as e:
        print(f"Error checking availability: {e}")
        raise HTTPException(status_code=400, detail="Invalid date or time format")

@api_router.put("/staff-breaks/{break_id}", response_model=StaffBreak)
async def update_staff_break(break_id: str, break_update: StaffBreakUpdate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing_break = await db.staff_breaks.find_one({"id": break_id})
    if not existing_break:
        raise HTTPException(status_code=404, detail="Staff break not found")
    
    update_data = {}
    for field, value in break_update.dict(exclude_unset=True).items():
        if value is not None:
            update_data[field] = prepare_for_mongo({field: value})[field]
    
    if update_data:
        await db.staff_breaks.update_one({"id": break_id}, {"$set": update_data})
    
    updated_break_data = await db.staff_breaks.find_one({"id": break_id})
    return StaffBreak(**parse_from_mongo(updated_break_data))

@api_router.delete("/staff-breaks/{break_id}")
async def delete_staff_break(break_id: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.staff_breaks.delete_one({"id": break_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Staff break not found")
    
    return {"message": "Staff break deleted successfully"}

# Revenue tracking and analytics
@api_router.get("/analytics/revenue")
async def get_revenue_analytics(
    period: str = "monthly",  # daily, weekly, monthly, yearly
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    staff_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get revenue analytics with various filters"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Set default date range if not provided
        if not start_date:
            if period == "daily":
                start_date = (datetime.now(timezone.utc) - timedelta(days=30)).date()
            elif period == "weekly":
                start_date = (datetime.now(timezone.utc) - timedelta(weeks=12)).date()
            elif period == "monthly":
                start_date = (datetime.now(timezone.utc) - timedelta(days=365)).date()
            else:  # yearly
                start_date = (datetime.now(timezone.utc) - timedelta(days=1095)).date()  # 3 years
        else:
            start_date = datetime.fromisoformat(start_date).date()
            
        if not end_date:
            end_date = datetime.now(timezone.utc).date()
        else:
            end_date = datetime.fromisoformat(end_date).date()
        
        # Build query
        query = {
            "booking_date": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            },
            "status": {"$in": ["confirmed", "completed"]},
            "payment_status": "paid"
        }
        
        if staff_id:
            query["staff_id"] = staff_id
        
        # Get bookings
        bookings = await db.bookings.find(query).to_list(length=None)
        
        # Calculate metrics
        total_revenue = sum(booking["total_price"] for booking in bookings)
        total_bookings = len(bookings)
        average_booking_value = total_revenue / total_bookings if total_bookings > 0 else 0
        
        # Group by period
        revenue_by_period = {}
        for booking in bookings:
            booking_date = datetime.fromisoformat(booking["booking_date"]).date()
            
            if period == "daily":
                key = booking_date.isoformat()
            elif period == "weekly":
                # Get Monday of the week
                week_start = booking_date - timedelta(days=booking_date.weekday())
                key = week_start.isoformat()
            elif period == "monthly":
                key = f"{booking_date.year}-{booking_date.month:02d}"
            else:  # yearly
                key = str(booking_date.year)
            
            if key not in revenue_by_period:
                revenue_by_period[key] = {"revenue": 0, "bookings": 0}
            
            revenue_by_period[key]["revenue"] += booking["total_price"]
            revenue_by_period[key]["bookings"] += 1
        
        # Get top services
        service_revenue = {}
        for booking in bookings:
            for service_id in booking["services"]:
                if service_id not in service_revenue:
                    service_revenue[service_id] = {"revenue": 0, "bookings": 0}
                service_revenue[service_id]["revenue"] += booking["total_price"] / len(booking["services"])
                service_revenue[service_id]["bookings"] += 1
        
        # Get service names
        services = await db.services.find().to_list(length=None)
        service_map = {s["id"]: s["name"] for s in services}
        
        top_services = [
            {
                "service_name": service_map.get(service_id, "Unknown"),
                "revenue": data["revenue"],
                "bookings": data["bookings"]
            }
            for service_id, data in sorted(service_revenue.items(), key=lambda x: x[1]["revenue"], reverse=True)[:5]
        ]
        
        # Get staff performance
        staff_revenue = {}
        for booking in bookings:
            staff_id = booking["staff_id"]
            if staff_id not in staff_revenue:
                staff_revenue[staff_id] = {"revenue": 0, "bookings": 0}
            staff_revenue[staff_id]["revenue"] += booking["total_price"]
            staff_revenue[staff_id]["bookings"] += 1
        
        # Get staff names
        staff_list = await db.staff.find().to_list(length=None)
        staff_map = {s["id"]: s["name"] for s in staff_list}
        
        staff_performance = [
            {
                "staff_name": staff_map.get(staff_id, "Unknown"),
                "staff_id": staff_id,
                "revenue": data["revenue"],
                "bookings": data["bookings"],
                "average_per_booking": data["revenue"] / data["bookings"] if data["bookings"] > 0 else 0
            }
            for staff_id, data in sorted(staff_revenue.items(), key=lambda x: x[1]["revenue"], reverse=True)
        ]
        
        return {
            "summary": {
                "total_revenue": total_revenue,
                "total_bookings": total_bookings,
                "average_booking_value": round(average_booking_value, 2),
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "revenue_by_period": [
                {"period": period, "revenue": data["revenue"], "bookings": data["bookings"]}
                for period, data in sorted(revenue_by_period.items())
            ],
            "top_services": top_services,
            "staff_performance": staff_performance
        }
        
    except Exception as e:
        print(f"Error in revenue analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate revenue analytics")

# Admin management route
@api_router.post("/admin/create-admin")
async def create_admin_user():
    """Create or update admin user - for initial setup only"""
    admin_email = "admin@frisorlafata.dk"
    admin_password = "admin123"
    
    # Check if admin already exists
    existing_admin = await db.users.find_one({"email": admin_email})
    
    if existing_admin:
        # Update existing user to admin
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"is_admin": True}}
        )
        return {"message": f"Updated {admin_email} to admin status"}
    else:
        # Create new admin user
        hashed_password = get_password_hash(admin_password)
        admin_user = {
            "id": str(uuid.uuid4()),
            "name": "Admin LaFata",
            "email": admin_email,
            "phone": "+45 12345678",
            "is_admin": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.users.insert_one(admin_user)
        await db.user_passwords.insert_one({
            "user_id": admin_user["id"], 
            "password": hashed_password
        })
        
        return {"message": f"Created admin user: {admin_email}"}

@api_router.post("/admin/make-admin/{user_email}")
async def make_user_admin(user_email: str):
    """Make any existing user an admin - for setup purposes"""
    result = await db.users.update_one(
        {"email": user_email},
        {"$set": {"is_admin": True}}
    )
    
    if result.modified_count > 0:
        return {"message": f"Successfully made {user_email} an admin"}
    else:
        raise HTTPException(status_code=404, detail="User not found")

# Initialize default data
@api_router.post("/admin/init-data")
async def initialize_default_data():
    """Initialize default staff, services, and email templates"""
    
    # Default staff
    default_staff = [
        {"name": "Lars Andersen", "specialty": "Klassisk klipning", "experience": "15 år"},
        {"name": "Mikael Jensen", "specialty": "Modern styling", "experience": "12 år"},
        {"name": "Sofia Nielsen", "specialty": "Farvning", "experience": "8 år"}
    ]
    
    for staff_data in default_staff:
        existing = await db.staff.find_one({"name": staff_data["name"]})
        if not existing:
            staff_obj = Staff(**staff_data)
            await db.staff.insert_one(prepare_for_mongo(staff_obj.dict()))
    
    # Default services
    default_services = [
        {"name": "Klipning", "duration_minutes": 30, "price": 350, "category": "haircut"},
        {"name": "Skæg trimning", "duration_minutes": 20, "price": 200, "category": "beard"},
        {"name": "Vask & styling", "duration_minutes": 45, "price": 400, "category": "styling"},
        {"name": "Farvning", "duration_minutes": 60, "price": 600, "category": "coloring"},
        {"name": "Børneklip", "duration_minutes": 25, "price": 250, "category": "haircut"},
        {"name": "Komplet styling", "duration_minutes": 90, "price": 750, "category": "premium"}
    ]
    
    for service_data in default_services:
        existing = await db.services.find_one({"name": service_data["name"]})
        if not existing:
            service_obj = Service(**service_data)
            await db.services.insert_one(prepare_for_mongo(service_obj.dict()))
    
    # Default email template
    template_data = {
        "name": "booking_confirmation",
        "subject": "Booking bekræftelse - Frisor LaFata",
        "content": """Hej {customer_name},

Din tid er blevet booket hos Frisor LaFata.

Dato: {booking_date}
Tid: {booking_time}
Frisør: {staff_name}

Vi ser frem til at se dig!

Med venlig hilsen,
Frisor LaFata""",
        "language": "da"
    }
    
    existing_template = await db.email_templates.find_one({"name": "booking_confirmation", "language": "da"})
    if not existing_template:
        template_obj = EmailTemplate(**template_data)
        await db.email_templates.insert_one(prepare_for_mongo(template_obj.dict()))
    
    return {"message": "Default data initialized successfully"}

# Email sending function
async def send_booking_confirmation(booking: Booking):
    """Send booking confirmation email"""
    if not EMAIL_CONFIG['email'] or not EMAIL_CONFIG['password']:
        return  # Email not configured
    
    try:
        # Get customer info
        customer = await db.users.find_one({"id": booking.customer_id})
        staff_member = await db.staff.find_one({"id": booking.staff_id})
        
        if not customer or not staff_member:
            return
        
        # Get email template
        template = await db.email_templates.find_one({"name": "booking_confirmation", "language": "da"})
        
        if template:
            subject = template["subject"]
            content = template["content"]
        else:
            # Default template
            subject = "Booking bekræftelse - Frisor LaFata"
            content = """
            Hej {customer_name},
            
            Din tid er blevet booket hos Frisor LaFata.
            
            Dato: {booking_date}
            Tid: {booking_time}
            Frisør: {staff_name}
            
            Vi ser frem til at se dig!
            
            Med venlig hilsen,
            Frisor LaFata
            """
        
        # Replace placeholders
        content = content.format(
            customer_name=customer["name"],
            booking_date=booking.booking_date,
            booking_time=booking.booking_time,
            staff_name=staff_member["name"]
        )
        
        # Send email
        msg = MIMEMultipart()
        msg['From'] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['email']}>"
        msg['To'] = customer["email"]
        msg['Subject'] = subject
        
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['email'], EMAIL_CONFIG['password'])
        server.send_message(msg)
        server.quit()
        
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()