from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile
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
BACKEND_URL = 'https://frisor-admin.preview.emergentagent.com'

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
app = FastAPI(title="Frisor LaFata API", version="1.0.0")
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
    specialty: str
    experience: str
    avatar_url: str = ""
    available_hours: dict = Field(default_factory=dict)  # {"monday": {"start": "09:00", "end": "17:00", "enabled": true}}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StaffCreate(BaseModel):
    name: str
    specialty: str
    experience: str
    avatar_url: str = ""
    available_hours: dict = Field(default_factory=dict)

class StaffUpdate(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    experience: Optional[str] = None
    avatar_url: Optional[str] = None
    available_hours: Optional[dict] = None

class Service(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    duration_minutes: int
    price: float
    description: str = ""
    category: str = "general"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ServiceCreate(BaseModel):
    name: str
    duration_minutes: int
    price: float
    description: str = ""
    category: str = "general"

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
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

class BookingUpdate(BaseModel):
    booking_date: Optional[date] = None
    booking_time: Optional[time] = None
    staff_id: Optional[str] = None
    status: Optional[str] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None
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

async def send_booking_email(booking: Booking, email_type: str):
    """Send booking email based on type (created, confirmed, changed, cancelled)"""
    try:
        # Get settings for email configuration and templates
        settings = await db.settings.find_one({"type": "site_settings"})
        if not settings:
            settings = SiteSettings().dict()
        
        # Check if email is configured
        if not settings.get('email_user') or not settings.get('email_password'):
            print("Email not configured, skipping booking email")
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
    avatar_url = f"{BACKEND_URL}/uploads/avatars/{filename}"
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
    video_url = f"{BACKEND_URL}/uploads/videos/{filename}"
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
    image_url = f"{BACKEND_URL}/uploads/images/{filename}"
    return {"image_url": image_url}

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
            "hero_image": ""
        }
    
    # Return only public settings (exclude sensitive data)
    public_settings = {
        "site_title": settings.get("site_title", "Frisor LaFata"),
        "site_description": settings.get("site_description", "Klassisk barbering siden 2010"),
        "contact_phone": settings.get("contact_phone", "+45 12 34 56 78"),
        "contact_email": settings.get("contact_email", "info@frisorlafata.dk"),
        "address": settings.get("address", "Hovedgaden 123, 1000 København"),
        "hero_title": settings.get("hero_title", "Klassisk Barbering"),
        "hero_subtitle": settings.get("hero_subtitle", "i Hjertet af Byen"),
        "hero_description": settings.get("hero_description", "Oplev den autentiske barber-oplevelse hos Frisor LaFata."),
        "hero_image": settings.get("hero_image", "")
    }
    
    return public_settings
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
                "return_url": f"https://frisor-admin.preview.emergentagent.com/payment/success?booking_id={booking_id}",
                "cancel_url": f"https://frisor-admin.preview.emergentagent.com/payment/cancel?booking_id={booking_id}"
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