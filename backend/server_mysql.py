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

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://frisorlafata.dk')

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
            query = "SELECT * FROM users WHERE email = %s"
            result = await execute_query(conn, query, (email,))
            if not result:
                raise HTTPException(status_code=401, detail="User not found")
            
            user = prepare_record_for_response(result[0])
            return User(**user)
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
        # Check users table
        query = "SELECT * FROM users WHERE email = %s"
        result = await execute_query(conn, query, (user_data.email,))
        
        if result:
            user = prepare_record_for_response(result[0])
            # Check password from user_passwords table
            pwd_query = "SELECT password FROM user_passwords WHERE user_id = %s"
            pwd_result = await execute_query(conn, pwd_query, (user['id'],))
            
            if pwd_result and verify_password(user_data.password, pwd_result[0]['password']):
                access_token = create_access_token(data={"sub": user['email']})
                return {"access_token": access_token, "token_type": "bearer", "user": user}
        
        raise HTTPException(status_code=401, detail="Invalid email or password")

# User endpoints
@api_router.get("/users", response_model=List[User])
async def get_users(admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        query = "SELECT * FROM users ORDER BY created_at DESC"
        result = await execute_query(conn, query)
        return [prepare_record_for_response(row) for row in result]

@api_router.post("/users", response_model=User)
async def create_user(user: UserCreate, admin_user: User = Depends(get_admin_user)):
    user_id = str(uuid.uuid4())
    
    async with get_db_connection() as conn:
        # Insert user
        user_data = prepare_data_for_insert(user.dict())
        user_data['id'] = user_id
        await insert_record(conn, 'users', user_data)
        
        # Insert password
        hashed_password = get_password_hash(user.password)
        await insert_record(conn, 'user_passwords', {
            'user_id': user_id,
            'password': hashed_password
        })
        
        query = "SELECT * FROM users WHERE id = %s"
        result = await execute_query(conn, query, (user_id,))
        return prepare_record_for_response(result[0])

@api_router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user: UserUpdate, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        user_data = prepare_data_for_insert({k: v for k, v in user.dict().items() if v is not None})
        await update_record(conn, 'users', user_data, user_id)
        
        query = "SELECT * FROM users WHERE id = %s"
        result = await execute_query(conn, query, (user_id,))
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        return prepare_record_for_response(result[0])

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        await delete_record(conn, 'user_passwords', user_id, 'user_id')
        await delete_record(conn, 'users', user_id)
        return {"message": "User deleted successfully"}

# Staff endpoints
@api_router.get("/staff", response_model=List[Staff])
async def get_staff():
    async with get_db_connection() as conn:
        query = "SELECT * FROM staff ORDER BY created_at DESC"
        result = await execute_query(conn, query)
        return [prepare_record_for_response(row) for row in result]

@api_router.post("/staff", response_model=Staff)
async def create_staff(staff: StaffCreate, admin_user: User = Depends(get_admin_user)):
    staff_id = str(uuid.uuid4())
    
    async with get_db_connection() as conn:
        staff_data = prepare_data_for_insert(staff.dict())
        staff_data['id'] = staff_id
        await insert_record(conn, 'staff', staff_data)
        
        query = "SELECT * FROM staff WHERE id = %s"
        result = await execute_query(conn, query, (staff_id,))
        return prepare_record_for_response(result[0])

@api_router.put("/staff/{staff_id}", response_model=Staff)
async def update_staff(staff_id: str, staff: StaffUpdate, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        staff_data = prepare_data_for_insert({k: v for k, v in staff.dict().items() if v is not None})
        await update_record(conn, 'staff', staff_data, staff_id)
        
        query = "SELECT * FROM staff WHERE id = %s"
        result = await execute_query(conn, query, (staff_id,))
        if not result:
            raise HTTPException(status_code=404, detail="Staff not found")
        return prepare_record_for_response(result[0])

@api_router.delete("/staff/{staff_id}")
async def delete_staff(staff_id: str, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        await delete_record(conn, 'staff', staff_id)
        return {"message": "Staff deleted successfully"}

# Services endpoints
@api_router.get("/services", response_model=List[Service])
async def get_services():
    async with get_db_connection() as conn:
        query = "SELECT * FROM services ORDER BY created_at DESC"
        result = await execute_query(conn, query)
        return [prepare_record_for_response(row) for row in result]

@api_router.post("/services", response_model=Service)
async def create_service(service: ServiceCreate, admin_user: User = Depends(get_admin_user)):
    service_id = str(uuid.uuid4())
    
    async with get_db_connection() as conn:
        service_data = prepare_data_for_insert(service.dict())
        service_data['id'] = service_id
        await insert_record(conn, 'services', service_data)
        
        query = "SELECT * FROM services WHERE id = %s"
        result = await execute_query(conn, query, (service_id,))
        return prepare_record_for_response(result[0])

@api_router.put("/services/{service_id}", response_model=Service)
async def update_service(service_id: str, service: ServiceUpdate, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        service_data = prepare_data_for_insert({k: v for k, v in service.dict().items() if v is not None})
        await update_record(conn, 'service', service_data, service_id)
        
        query = "SELECT * FROM services WHERE id = %s"
        result = await execute_query(conn, query, (service_id,))
        if not result:
            raise HTTPException(status_code=404, detail="Service not found")
        return prepare_record_for_response(result[0])

@api_router.delete("/services/{service_id}")
async def delete_service(service_id: str, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        await delete_record(conn, 'services', service_id)
        return {"message": "Service deleted successfully"}

# Bookings endpoints
@api_router.get("/bookings", response_model=List[Booking])
async def get_bookings(admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        query = "SELECT * FROM bookings ORDER BY date DESC, time DESC"
        result = await execute_query(conn, query)
        return [prepare_record_for_response(row) for row in result]

@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking: BookingCreate):
    booking_id = str(uuid.uuid4())
    
    async with get_db_connection() as conn:
        booking_data = prepare_data_for_insert(booking.dict())
        booking_data['id'] = booking_id
        await insert_record(conn, 'bookings', booking_data)
        
        query = "SELECT * FROM bookings WHERE id = %s"
        result = await execute_query(conn, query, (booking_id,))
        return prepare_record_for_response(result[0])

@api_router.put("/bookings/{booking_id}", response_model=Booking)
async def update_booking(booking_id: str, booking: BookingUpdate, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        booking_data = prepare_data_for_insert({k: v for k, v in booking.dict().items() if v is not None})
        await update_record(conn, 'bookings', booking_data, booking_id)
        
        query = "SELECT * FROM bookings WHERE id = %s"
        result = await execute_query(conn, query, (booking_id,))
        if not result:
            raise HTTPException(status_code=404, detail="Booking not found")
        return prepare_record_for_response(result[0])

@api_router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        await delete_record(conn, 'bookings', booking_id)
        return {"message": "Booking deleted successfully"}

# Settings endpoints
@api_router.get("/settings", response_model=SiteSettings)
async def get_settings(admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        query = "SELECT * FROM settings LIMIT 1"
        result = await execute_query(conn, query)
        if result:
            return prepare_record_for_response(result[0])
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
                'home_service_description': 'Vi kommer til dig! Oplev professionel barbering i dit eget hjem.'
            }
            await insert_record(conn, 'settings', default_settings)
            return prepare_record_for_response(default_settings)

@api_router.put("/settings", response_model=SiteSettings)
async def update_settings(settings: SettingsUpdate, admin_user: User = Depends(get_admin_user)):
    async with get_db_connection() as conn:
        query = "SELECT * FROM settings LIMIT 1"
        result = await execute_query(conn, query)
        
        if result:
            settings_data = prepare_data_for_insert({k: v for k, v in settings.dict().items() if v is not None})
            await update_record(conn, 'settings', settings_data, result[0]['id'])
            
            query = "SELECT * FROM settings WHERE id = %s"
            updated_result = await execute_query(conn, query, (result[0]['id'],))
            return prepare_record_for_response(updated_result[0])
        else:
            raise HTTPException(status_code=404, detail="Settings not found")

@api_router.get("/public/settings")
async def get_public_settings():
    async with get_db_connection() as conn:
        query = "SELECT * FROM settings LIMIT 1"
        result = await execute_query(conn, query)
        if result:
            settings = prepare_record_for_response(result[0])
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
                'home_service_description': settings.get('home_service_description', 'Vi kommer til dig! Oplev professionel barbering i dit eget hjem.')
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

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Frisor LaFata API", "status": "running"}

@app.get("/api")
async def api_root():
    return {"message": "Frisor LaFata API v1.0", "endpoints": ["auth", "users", "staff", "services", "bookings", "settings"]}

# Include API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)