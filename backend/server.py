from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, date, time
import jwt
from passlib.context import CryptContext
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    'sandbox_mode': True  # Will be configurable
}

# Create the main app
app = FastAPI(title="Frisor LaFata API", version="1.0.0")
api_router = APIRouter(prefix="/api")

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
    available_hours: dict = Field(default_factory=dict)  # {"monday": ["09:00", "17:00"]}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StaffCreate(BaseModel):
    name: str
    specialty: str
    experience: str
    available_hours: dict = Field(default_factory=dict)

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

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str
    staff_id: str
    services: List[str]  # List of service IDs
    booking_date: date
    booking_time: time
    total_duration: int
    total_price: float
    payment_method: str = "cash"  # "cash", "paypal"
    payment_status: str = "pending"  # "pending", "paid", "cancelled"
    status: str = "confirmed"  # "confirmed", "cancelled", "completed"
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BookingCreate(BaseModel):
    customer_id: str
    staff_id: str
    services: List[str]
    booking_date: date
    booking_time: time
    payment_method: str = "cash"
    notes: str = ""

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
    admin_emails = ["admin@frisorlafata.dk", "admin2@frisorlafata.dk"]
    
    # Create user
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict.pop('password')
    if user_count == 0 or user.email in admin_emails:  # First user or admin email becomes admin
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

# Booking routes
@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking: BookingCreate):
    # Calculate total duration and price
    services = await db.services.find({"id": {"$in": booking.services}}).to_list(length=None)
    if len(services) != len(booking.services):
        raise HTTPException(status_code=400, detail="One or more services not found")
    
    total_duration = sum(service["duration_minutes"] for service in services)
    total_price = sum(service["price"] for service in services)
    
    # Check if slot is available
    existing_booking = await db.bookings.find_one({
        "staff_id": booking.staff_id,
        "booking_date": booking.booking_date.isoformat(),
        "booking_time": booking.booking_time.strftime('%H:%M:%S'),
        "status": {"$ne": "cancelled"}
    })
    
    if existing_booking:
        raise HTTPException(status_code=400, detail="Time slot not available")
    
    booking_dict = booking.dict()
    booking_dict.update({
        "total_duration": total_duration,
        "total_price": total_price
    })
    
    booking_obj = Booking(**booking_dict)
    await db.bookings.insert_one(prepare_for_mongo(booking_obj.dict()))
    
    # Send confirmation email (if configured)
    await send_booking_confirmation(booking_obj)
    
    return booking_obj

@api_router.get("/bookings", response_model=List[Booking])
async def get_bookings(current_user: User = Depends(get_current_user)):
    if current_user.is_admin:
        bookings = await db.bookings.find().to_list(length=None)
    else:
        bookings = await db.bookings.find({"customer_id": current_user.id}).to_list(length=None)
    
    return [Booking(**parse_from_mongo(booking)) for booking in bookings]

@api_router.get("/bookings/available-slots")
async def get_available_slots(staff_id: str, date: str):
    """Get available time slots for a specific staff member and date"""
    booking_date = datetime.fromisoformat(date).date()
    day_name = booking_date.strftime('%A').lower()
    
    # Check if staff works on this day
    staff_member = await db.staff.find_one({"id": staff_id})
    if not staff_member:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
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
    from datetime import datetime, timedelta
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

# PayPal integration placeholder
@api_router.post("/payments/paypal/create")
async def create_paypal_payment(booking_id: str):
    """Create PayPal payment (placeholder for now)"""
    # This will be implemented with actual PayPal SDK
    return {
        "payment_id": f"PAYPAL_{booking_id}",
        "approval_url": f"https://www.sandbox.paypal.com/checkoutnow?token=example",
        "sandbox_mode": PAYPAL_CONFIG["sandbox_mode"]
    }

# Initialize default data
@api_router.post("/admin/init-data")
async def initialize_default_data(current_user: User = Depends(get_current_user)):
    """Initialize default staff, services, and email templates"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
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