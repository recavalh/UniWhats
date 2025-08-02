from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Request, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
from datetime import datetime, timedelta
import os
from typing import List, Optional, Dict, Any
import uuid
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

# Custom JSON encoder for FastAPI responses
from fastapi.encoders import jsonable_encoder

from fastapi.responses import JSONResponse
import json
from bson import ObjectId

def clean_document(doc):
    """Remove MongoDB ObjectId fields and convert datetime objects"""
    if doc is None:
        return None
    
    if isinstance(doc, dict):
        cleaned = {}
        for key, value in doc.items():
            if key == '_id':
                continue  # Skip ObjectId fields
            elif isinstance(value, ObjectId):
                cleaned[key] = str(value)
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, dict):
                cleaned[key] = clean_document(value)
            elif isinstance(value, list):
                cleaned[key] = [clean_document(item) for item in value]
            else:
                cleaned[key] = value
        return cleaned
    elif isinstance(doc, list):
        return [clean_document(item) for item in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, datetime):
        return doc.isoformat()
    else:
        return doc

def clean_documents(docs):
    """Remove MongoDB ObjectId fields from a list of documents"""
    return clean_document(docs)

# Environment variables
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DATABASE_NAME = "uniwhats_desk"

app = FastAPI(title="UniWhats Desk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
client = AsyncIOMotorClient(MONGO_URL)
db = client[DATABASE_NAME]

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class User(BaseModel):
    id: str
    name: str
    email: str
    role: str  # Agent, Coordinator, Sales Rep, Receptionist, Manager
    department_id: Optional[str] = None
    avatar: Optional[str] = None

class Department(BaseModel):
    id: str
    name: str
    description: str
    business_hours: dict
    active: bool = True

class Contact(BaseModel):
    id: str
    wa_id: str
    phone: str
    name: str
    student_id: Optional[str] = None
    tags: List[str] = []
    custom_fields: dict = {}
    created_at: datetime

class Message(BaseModel):
    id: str
    conversation_id: str
    direction: str  # 'in' or 'out'
    body: str
    type: str  # 'text', 'image', 'document'
    media_url: Optional[str] = None
    timestamp: datetime
    sender_user_id: Optional[str] = None
    read_status: bool = False

class Conversation(BaseModel):
    id: str
    contact_id: str
    department_id: str
    status: str  # 'open', 'closed'
    assignee_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime
    sla_due_at: Optional[datetime] = None
    tags: List[str] = []

class Note(BaseModel):
    id: str
    conversation_id: str
    author_user_id: str
    body: str
    created_at: datetime

class LoginRequest(BaseModel):
    email: str
    password: str

class MessageRequest(BaseModel):
    body: str
    type: str = "text"

class AssignRequest(BaseModel):
    assignee_user_id: Optional[str] = None
    department_id: Optional[str] = None

# Mock data initialization
async def init_mock_data():
    # Departments
    departments = [
        {
            "id": "dept_reception",
            "name": "Reception & Finance",
            "description": "First contact and financial inquiries",
            "business_hours": {"start": "08:00", "end": "18:00"},
            "active": True
        },
        {
            "id": "dept_coordination",
            "name": "Coordination",
            "description": "Academic coordination and cancellations",
            "business_hours": {"start": "09:00", "end": "17:00"},
            "active": True
        },
        {
            "id": "dept_sales",
            "name": "Sales",
            "description": "Enrollment and sales inquiries",
            "business_hours": {"start": "08:00", "end": "19:00"},
            "active": True
        },
        {
            "id": "dept_management",
            "name": "Management",
            "description": "Administrative and management issues",
            "business_hours": {"start": "09:00", "end": "17:00"},
            "active": True
        }
    ]
    
    # Users
    users = [
        {
            "id": "user_maria",
            "name": "Maria Silva",
            "email": "maria@school.com",
            "password_hash": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "Receptionist",
            "department_id": "dept_reception",
            "avatar": "https://images.unsplash.com/photo-1494790108755-2616b7b6ca85?w=150&h=150&fit=crop&crop=face"
        },
        {
            "id": "user_carlos",
            "name": "Carlos Santos",
            "email": "carlos@school.com",
            "password_hash": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "Coordinator",
            "department_id": "dept_coordination",
            "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face"
        },
        {
            "id": "user_ana",
            "name": "Ana Costa",
            "email": "ana@school.com",
            "password_hash": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "Sales Rep",
            "department_id": "dept_sales",
            "avatar": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face"
        },
        {
            "id": "user_admin",
            "name": "João Diretor",
            "email": "admin@school.com",
            "password_hash": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "Manager",
            "department_id": None,
            "avatar": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face"
        }
    ]
    
    # Contacts
    contacts = [
        {
            "id": "contact_parent1",
            "wa_id": "5511987654321",
            "phone": "+55 11 98765-4321",
            "name": "Patricia Almeida",
            "student_id": "STU001",
            "tags": ["parent", "grade5"],
            "custom_fields": {"student_name": "Lucas Almeida", "grade": "5º Ano"},
            "created_at": datetime.now() - timedelta(days=30)
        },
        {
            "id": "contact_parent2", 
            "wa_id": "5511876543210",
            "phone": "+55 11 87654-3210",
            "name": "Roberto Fernandes",
            "student_id": "STU002",
            "tags": ["parent", "grade8"],
            "custom_fields": {"student_name": "Sofia Fernandes", "grade": "8º Ano"},
            "created_at": datetime.now() - timedelta(days=15)
        },
        {
            "id": "contact_prospect",
            "wa_id": "5511765432109",
            "phone": "+55 11 76543-2109",
            "name": "Amanda Silva",
            "tags": ["prospect", "elementary"],
            "custom_fields": {"interest": "Ensino Fundamental", "child_age": "7 anos"},
            "created_at": datetime.now() - timedelta(days=3)
        }
    ]
    
    # Conversations
    conversations = [
        {
            "id": "conv_001",
            "contact_id": "contact_parent1",
            "department_id": "dept_coordination",
            "status": "open",
            "assignee_user_id": "user_carlos",
            "created_at": datetime.now() - timedelta(hours=2),
            "updated_at": datetime.now() - timedelta(minutes=15),
            "last_message_at": datetime.now() - timedelta(minutes=15),
            "sla_due_at": datetime.now() + timedelta(hours=2),
            "tags": ["cancellation", "urgent"]
        },
        {
            "id": "conv_002",
            "contact_id": "contact_parent2",
            "department_id": "dept_reception",
            "status": "open",
            "assignee_user_id": None,
            "created_at": datetime.now() - timedelta(hours=1),
            "updated_at": datetime.now() - timedelta(minutes=5),
            "last_message_at": datetime.now() - timedelta(minutes=5),
            "sla_due_at": datetime.now() + timedelta(hours=3),
            "tags": ["payment"]
        },
        {
            "id": "conv_003",
            "contact_id": "contact_prospect",
            "department_id": "dept_sales",
            "status": "open",
            "assignee_user_id": "user_ana",
            "created_at": datetime.now() - timedelta(minutes=30),
            "updated_at": datetime.now() - timedelta(minutes=10),
            "last_message_at": datetime.now() - timedelta(minutes=10),
            "sla_due_at": datetime.now() + timedelta(hours=4),
            "tags": ["lead", "hot"]
        }
    ]
    
    # Messages
    messages = [
        # Conversation 1: Cancellation request
        {
            "id": "msg_001",
            "conversation_id": "conv_001", 
            "direction": "in",
            "body": "Boa tarde! Preciso cancelar a matrícula do Lucas. Por favor, me informem sobre o processo.",
            "type": "text",
            "timestamp": datetime.now() - timedelta(hours=2),
            "sender_user_id": None,
            "read_status": True
        },
        {
            "id": "msg_002",
            "conversation_id": "conv_001",
            "direction": "out", 
            "body": "Olá Patricia! Entendo sua situação. Para processar o cancelamento, preciso de alguns documentos. Pode me enviar uma foto do RG do responsável?",
            "type": "text",
            "timestamp": datetime.now() - timedelta(minutes=15),
            "sender_user_id": "user_carlos",
            "read_status": True
        },
        
        # Conversation 2: Payment inquiry
        {
            "id": "msg_003",
            "conversation_id": "conv_002",
            "direction": "in",
            "body": "Bom dia! Recebi uma cobrança diferente este mês. Podem me explicar o que aconteceu?",
            "type": "text",
            "timestamp": datetime.now() - timedelta(hours=1),
            "sender_user_id": None,
            "read_status": False
        },
        {
            "id": "msg_004",
            "conversation_id": "conv_002",
            "direction": "in",
            "body": "Segue a foto da fatura que recebi",
            "type": "image",
            "media_url": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=300&h=200&fit=crop",
            "timestamp": datetime.now() - timedelta(minutes=5),
            "sender_user_id": None,
            "read_status": False
        },
        
        # Conversation 3: Sales lead
        {
            "id": "msg_005",
            "conversation_id": "conv_003",
            "direction": "in",  
            "body": "Olá! Gostaria de informações sobre vagas para o ensino fundamental. Minha filha tem 7 anos.",
            "type": "text",
            "timestamp": datetime.now() - timedelta(minutes=30),
            "sender_user_id": None,
            "read_status": True
        },
        {
            "id": "msg_006",
            "conversation_id": "conv_003",
            "direction": "out",
            "body": "Olá Amanda! Que bom saber do seu interesse! Temos vagas disponíveis no 2º ano. Gostaria de agendar uma visita para conhecer nossa escola?",
            "type": "text", 
            "timestamp": datetime.now() - timedelta(minutes=10),
            "sender_user_id": "user_ana",
            "read_status": True
        }
    ]
    
    # Clear existing data and insert mock data
    await db.departments.delete_many({})
    await db.users.delete_many({})
    await db.contacts.delete_many({})
    await db.conversations.delete_many({})
    await db.messages.delete_many({})
    
    await db.departments.insert_many(departments)
    await db.users.insert_many(users)
    await db.contacts.insert_many(contacts)
    await db.conversations.insert_many(conversations)
    await db.messages.insert_many(messages)

# Initialize mock data on startup
@app.on_event("startup")
async def startup_event():
    await init_mock_data()

# Authentication endpoints
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    user = await db.users.find_one({"email": request.email})
    if not user or not bcrypt.checkpw(request.password.encode('utf-8'), user["password_hash"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Remove password hash from response
    user.pop("password_hash")
    
    # Create a simple JWT-like token with user ID
    token = f"uniwhats_{user['id']}_{uuid.uuid4().hex[:16]}"
    
    return {"user": clean_document(user), "token": token}

@app.post("/api/auth/forgot-password")
async def forgot_password(email_data: dict):
    email = email_data.get("email")
    user = await db.users.find_one({"email": email})
    
    if not user:
        # Don't reveal if email exists or not for security
        return {"success": True, "message": "If the email exists, a reset link has been sent."}
    
    # Generate temporary password
    temp_password = f"temp{uuid.uuid4().hex[:8]}"
    password_hash = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update password
    await db.users.update_one(
        {"email": email},
        {"$set": {"password_hash": password_hash, "password_reset_required": True}}
    )
    
    # Mock email sending
    print(f"📧 Password reset email sent to {email}")
    print(f"   Temporary password: {temp_password}")
    
    return {
        "success": True, 
        "message": "If the email exists, a reset link has been sent.",
        "temp_password": temp_password  # In production, don't return this
    }

@app.post("/api/auth/logout")
async def logout():
    # In a real app, you'd invalidate the token here
    return {"success": True, "message": "Logged out successfully"}

@app.get("/api/auth/me")
async def get_current_user(request: Request):
    # Extract user ID from token
    authorization = request.headers.get("authorization") or request.headers.get("Authorization")
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        if token.startswith("uniwhats_"):
            try:
                # Extract user ID from token format: uniwhats_{user_id}_{random}
                # Token format is: uniwhats_user_admin_random or uniwhats_user_maria_random
                parts = token.split("_")
                if len(parts) >= 4:
                    # Reconstruct user_id from parts 1 and 2: user_admin, user_maria, etc.
                    user_id = f"{parts[1]}_{parts[2]}"
                    user = await db.users.find_one({"id": user_id})
                    if user:
                        user.pop("password_hash", None)
                        print(f"✅ Token authentication successful for user: {user.get('name')} ({user.get('id')})")
                        return clean_document(user)
                    else:
                        print(f"❌ User not found for ID: {user_id}")
                else:
                    print(f"❌ Invalid token format: {token}")
            except Exception as e:
                print(f"❌ Token parsing error: {e}")
    
    # Return 401 instead of fallback for security
    print("❌ No valid token found, returning 401")
    raise HTTPException(status_code=401, detail="Authentication required")

@app.put("/api/users/{user_id}/profile")
async def update_user_profile(user_id: str, profile_data: dict, request: Request):
    # Extract current user from token
    authorization = request.headers.get("authorization") or request.headers.get("Authorization")
    current_user_id = None
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        if token.startswith("uniwhats_"):
            try:
                current_user_id = token.split("_")[1]
            except:
                pass
    
    # Users can only edit their own profile (or admin can edit any)
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    if current_user_id != user_id and current_user.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Can only edit your own profile")
    
    # Update user profile
    update_data = {}
    if "name" in profile_data:
        update_data["name"] = profile_data["name"].strip()
    if "email" in profile_data:
        # Check if email is already taken by another user
        existing_user = await db.users.find_one({"email": profile_data["email"], "id": {"$ne": user_id}})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        update_data["email"] = profile_data["email"].strip()
    if "avatar" in profile_data:
        update_data["avatar"] = profile_data["avatar"]
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    update_data["updated_at"] = datetime.now()
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return updated user data
    updated_user = await db.users.find_one({"id": user_id})
    updated_user.pop("password_hash", None)
    
    return clean_document(updated_user)

# Conversations endpoints
@app.get("/api/conversations")
async def get_conversations(
    department_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    status: Optional[str] = None,
    unassigned: bool = False
):
    query = {}
    if department_id:
        query["department_id"] = department_id
    if assignee_id:
        query["assignee_user_id"] = assignee_id
    if status:
        query["status"] = status
    if unassigned:
        query["assignee_user_id"] = None
        
    conversations = await db.conversations.find(query).sort("last_message_at", -1).to_list(100)
    
    # Enrich with contact and user data
    for conv in conversations:
        contact = await db.contacts.find_one({"id": conv["contact_id"]})
        conv["contact"] = contact
        
        if conv.get("assignee_user_id"):
            assignee = await db.users.find_one({"id": conv["assignee_user_id"]})
            if assignee:
                assignee.pop("password_hash", None)
                conv["assignee"] = assignee
        
        department = await db.departments.find_one({"id": conv["department_id"]})
        conv["department"] = department
        
        # Get unread message count
        unread_count = await db.messages.count_documents({
            "conversation_id": conv["id"],
            "direction": "in", 
            "read_status": False
        })
        conv["unread_count"] = unread_count
        
        # Get last message
        last_msg = await db.messages.find_one(
            {"conversation_id": conv["id"]},
            sort=[("timestamp", -1)]
        )
        conv["last_message"] = last_msg
    
    cleaned_data = clean_documents(conversations)
    return JSONResponse(content=cleaned_data)

@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str):
    messages = await db.messages.find({"conversation_id": conversation_id}).sort("timestamp", 1).to_list(100)
    
    # Enrich with sender data
    for msg in messages:
        if msg.get("sender_user_id"):
            sender = await db.users.find_one({"id": msg["sender_user_id"]})
            if sender:
                sender.pop("password_hash", None)
                msg["sender"] = sender
    
    return clean_documents(messages)

@app.post("/api/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, request: MessageRequest):
    # Mock current user
    current_user_id = "user_admin"
    
    message = {
        "_id": f"msg_{uuid.uuid4().hex[:8]}",
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "conversation_id": conversation_id,
        "direction": "out",
        "body": request.body,
        "type": request.type,
        "timestamp": datetime.now(),
        "sender_user_id": current_user_id,
        "read_status": True
    }
    
    await db.messages.insert_one(message)
    
    # Update conversation last_message_at
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"last_message_at": datetime.now(), "updated_at": datetime.now()}}
    )
    
    # Broadcast update
    await manager.broadcast({
        "type": "new_message",
        "conversation_id": conversation_id,
        "message": clean_document(message)
    })
    
    return JSONResponse(content=clean_document(message))

@app.post("/api/conversations/{conversation_id}/assign")
async def assign_conversation(conversation_id: str, request: AssignRequest):
    update_data = {"updated_at": datetime.now()}
    
    if request.assignee_user_id is not None:
        update_data["assignee_user_id"] = request.assignee_user_id
    
    if request.department_id:
        update_data["department_id"] = request.department_id
    
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": update_data}
    )
    
    # Broadcast update
    await manager.broadcast({
        "type": "conversation_updated",
        "conversation_id": conversation_id,
        "update": update_data
    })
    
    return {"success": True}

@app.post("/api/conversations/{conversation_id}/close")
async def close_conversation(conversation_id: str):
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"status": "closed", "updated_at": datetime.now()}}
    )
    
    await manager.broadcast({
        "type": "conversation_updated", 
        "conversation_id": conversation_id,
        "update": {"status": "closed"}
    })
    
    return {"success": True}

@app.post("/api/conversations/{conversation_id}/reopen")
async def reopen_conversation(conversation_id: str):
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"status": "open", "updated_at": datetime.now()}}
    )
    
    await manager.broadcast({
        "type": "conversation_updated",
        "conversation_id": conversation_id, 
        "update": {"status": "open"}
    })
    
    return {"success": True}

@app.post("/api/conversations/{conversation_id}/mark-read")
async def mark_messages_read(conversation_id: str):
    await db.messages.update_many(
        {"conversation_id": conversation_id, "direction": "in"},
        {"$set": {"read_status": True}}
    )
    
    await manager.broadcast({
        "type": "messages_read",
        "conversation_id": conversation_id
    })
    
    return {"success": True}

# Departments endpoints
@app.get("/api/departments")
async def get_departments():
    departments = await db.departments.find({}).to_list(10)  # Show all departments, not just active
    return clean_documents(departments)

# Users endpoints
@app.get("/api/users")
async def get_users():
    users = await db.users.find({}).to_list(100)
    for user in users:
        user.pop("password_hash", None)
    return clean_documents(users)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Mock WhatsApp webhook simulation
@app.post("/api/mock/send-message")
async def mock_send_whatsapp_message(contact_id: str, message: str, message_type: str = "text"):
    """Simulate receiving a WhatsApp message"""
    
    # Find or create conversation
    conversation = await db.conversations.find_one({"contact_id": contact_id, "status": "open"})
    
    if not conversation:
        # Create new conversation in Reception department
        conversation = {
            "id": f"conv_{uuid.uuid4().hex[:8]}",
            "contact_id": contact_id,
            "department_id": "dept_reception",
            "status": "open",
            "assignee_user_id": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_message_at": datetime.now(),
            "sla_due_at": datetime.now() + timedelta(hours=4),
            "tags": []
        }
        await db.conversations.insert_one(conversation)
    
    # Create incoming message
    msg = {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "conversation_id": conversation["id"],
        "direction": "in",
        "body": message,
        "type": message_type,
        "timestamp": datetime.now(),
        "sender_user_id": None,
        "read_status": False
    }
    
    await db.messages.insert_one(msg)
    
    # Update conversation
    await db.conversations.update_one(
        {"id": conversation["id"]},
        {"$set": {"last_message_at": datetime.now(), "updated_at": datetime.now()}}
    )
    
    # Broadcast new conversation or message
    await manager.broadcast({
        "type": "new_message",
        "conversation_id": conversation["id"],
        "message": msg
    })
    
    return {"success": True, "conversation_id": conversation["id"]}

# Settings and Admin endpoints
@app.get("/api/admin/users")
async def get_all_users_admin(current_user_id: str = "user_admin"):  # Mock admin check
    # Check if current user is admin
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user or current_user.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
    
    users = await db.users.find({}).to_list(100)
    for user in users:
        user.pop("password_hash", None)
        # Get department info
        if user.get("department_id"):
            dept = await db.departments.find_one({"id": user["department_id"]})
            user["department"] = dept
    
    return clean_documents(users)

@app.post("/api/admin/users")
async def create_user_admin(user_data: dict, current_user_id: str = "user_admin"):
    # Check if current user is admin
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user or current_user.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data["email"]})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user
    new_user = {
        "_id": f"user_{uuid.uuid4().hex[:8]}",
        "id": f"user_{uuid.uuid4().hex[:8]}",
        "name": user_data["name"],
        "email": user_data["email"],
        "password_hash": bcrypt.hashpw(user_data["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": user_data["role"],
        "department_id": user_data.get("department_id"),
        "avatar": user_data.get("avatar", f"https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face"),
        "created_at": datetime.now(),
        "active": True
    }
    
    await db.users.insert_one(new_user)
    new_user.pop("password_hash", None)
    
    return JSONResponse(content=clean_document(new_user))

@app.put("/api/admin/users/{user_id}")
async def update_user_admin(user_id: str, user_data: dict, current_user_id: str = "user_admin"):
    # Check if current user is admin
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user or current_user.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
    
    # Update user
    update_data = {
        "name": user_data["name"],
        "email": user_data["email"],
        "role": user_data["role"],
        "department_id": user_data.get("department_id"),
        "updated_at": datetime.now()
    }
    
    # Update password if provided
    if user_data.get("password"):
        update_data["password_hash"] = bcrypt.hashpw(user_data["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"success": True}

@app.delete("/api/admin/users/{user_id}")
async def delete_user_admin(user_id: str, current_user_id: str = "user_admin"):
    # Check if current user is admin
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user or current_user.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
    
    # Don't allow deleting self
    if user_id == current_user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    result = await db.users.delete_one({"id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"success": True}

@app.post("/api/admin/users/{user_id}/reset-password")
async def reset_user_password(user_id: str, current_user_id: str = "user_admin"):
    # Check if current user is admin
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user or current_user.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
    
    # Find user
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate temporary password
    temp_password = f"temp{uuid.uuid4().hex[:8]}"
    password_hash = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update password
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"password_hash": password_hash, "password_reset_required": True}}
    )
    
    # Mock email sending
    print(f"📧 Password reset email sent to {user['email']}")
    print(f"   Temporary password: {temp_password}")
    
    return {
        "success": True, 
        "message": f"Password reset email sent to {user['email']}",
        "temp_password": temp_password  # In production, don't return this
    }

# Department admin endpoints
@app.post("/api/admin/departments")
async def create_department_admin(dept_data: dict, current_user_id: str = "user_admin"):
    # Check if current user is admin
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user or current_user.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
    
    new_dept = {
        "_id": f"dept_{uuid.uuid4().hex[:8]}",
        "id": f"dept_{uuid.uuid4().hex[:8]}",
        "name": dept_data["name"],
        "description": dept_data["description"],
        "active": dept_data.get("active", True),
        "business_hours": dept_data.get("business_hours", {"start": "09:00", "end": "17:00"}),
        "created_at": datetime.now()
    }
    
    await db.departments.insert_one(new_dept)
    
    return JSONResponse(content=clean_document(new_dept))

@app.put("/api/admin/departments/{dept_id}")
async def update_department_admin(dept_id: str, dept_data: dict, current_user_id: str = "user_admin"):
    # Check if current user is admin
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user or current_user.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
    
    update_data = {
        "name": dept_data["name"],
        "description": dept_data["description"],
        "active": dept_data.get("active", True),
        "business_hours": dept_data.get("business_hours", {"start": "09:00", "end": "17:00"}),
        "updated_at": datetime.now()
    }
    
    result = await db.departments.update_one(
        {"id": dept_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")
    
    return {"success": True}

@app.post("/api/admin/departments/{dept_id}/toggle")
async def toggle_department_status(dept_id: str, current_user_id: str = "user_admin"):
    # Check if current user is admin
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user or current_user.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
    
    # Get current department status
    dept = await db.departments.find_one({"id": dept_id})
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Toggle the active status
    new_status = not dept.get("active", True)
    
    result = await db.departments.update_one(
        {"id": dept_id},
        {"$set": {"active": new_status, "updated_at": datetime.now()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")
    
@app.delete("/api/admin/departments/{dept_id}")
async def delete_department_admin(dept_id: str, current_user_id: str = "user_admin"):
    # Check if current user is admin
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user or current_user.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
    
    # Check if department has users
    users_count = await db.users.count_documents({"department_id": dept_id})
    if users_count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete department with {users_count} active users")
    
    result = await db.departments.delete_one({"id": dept_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")
    
# WhatsApp Settings and Webhook endpoints
@app.get("/api/admin/whatsapp/settings")
async def get_whatsapp_settings(current_user_id: str = "user_admin"):
    # Check if current user is admin
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user or current_user.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
    
    # Get WhatsApp settings from database
    settings = await db.whatsapp_settings.find_one({"type": "credentials"})
    
    if not settings:
        # Return empty settings if none exist
        return {
            "phone_number_id": "",
            "business_account_id": "",
            "api_token": "",
            "verify_token": "",
            "webhook_url": "https://uni-whats.vercel.app/webhooks/whatsapp",
            "configured": False
        }
    
    # Mask sensitive tokens for display
    masked_settings = {
        "phone_number_id": settings.get("phone_number_id", ""),
        "business_account_id": settings.get("business_account_id", ""),
        "api_token": "••••••••" + settings.get("api_token", "")[-4:] if settings.get("api_token") else "",
        "verify_token": "••••••••" + settings.get("verify_token", "")[-4:] if settings.get("verify_token") else "",
        "webhook_url": "https://uni-whats.vercel.app/webhooks/whatsapp",
        "configured": bool(settings.get("api_token") and settings.get("verify_token"))
    }
    
    return clean_document(masked_settings)

@app.post("/api/admin/whatsapp/settings")
async def save_whatsapp_settings(settings_data: dict, current_user_id: str = "user_admin"):
    # Check if current user is admin
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user or current_user.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
    
    # Validate required fields
    required_fields = ["phone_number_id", "business_account_id", "api_token", "verify_token"]
    for field in required_fields:
        if not settings_data.get(field, "").strip():
            raise HTTPException(status_code=400, detail=f"Field '{field}' is required")
    
    # Prepare settings for storage
    whatsapp_settings = {
        "_id": "whatsapp_credentials",
        "type": "credentials",
        "phone_number_id": settings_data["phone_number_id"].strip(),
        "business_account_id": settings_data["business_account_id"].strip(),
        "api_token": settings_data["api_token"].strip(),
        "verify_token": settings_data["verify_token"].strip(),
        "updated_at": datetime.now(),
        "updated_by": current_user_id
    }
    
    # Store or update settings
    await db.whatsapp_settings.replace_one(
        {"type": "credentials"},
        whatsapp_settings,
        upsert=True
    )
    
    # Set environment variables for immediate use
    os.environ["WHATSAPP_PHONE_NUMBER_ID"] = whatsapp_settings["phone_number_id"]
    os.environ["WHATSAPP_BUSINESS_ACCOUNT_ID"] = whatsapp_settings["business_account_id"]
    os.environ["WHATSAPP_API_TOKEN"] = whatsapp_settings["api_token"]
    os.environ["WHATSAPP_VERIFY_TOKEN"] = whatsapp_settings["verify_token"]
    
    return {"success": True, "message": "WhatsApp settings saved successfully"}

@app.post("/api/admin/whatsapp/test-connection")
async def test_whatsapp_connection(current_user_id: str = "user_admin"):
    # Check if current user is admin
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user or current_user.get("role") != "Manager":
        raise HTTPException(status_code=403, detail="Access denied. Admin role required.")
    
    # Get settings
    settings = await db.whatsapp_settings.find_one({"type": "credentials"})
    if not settings or not settings.get("api_token"):
        raise HTTPException(status_code=400, detail="WhatsApp credentials not configured")
    
    # Test WhatsApp API connection
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {settings['api_token']}",
                "Content-Type": "application/json"
            }
            
            # Test by getting business account info
            response = await client.get(
                f"https://graph.facebook.com/v17.0/{settings['business_account_id']}",
                headers=headers
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "WhatsApp API connection successful"}
            else:
                return {"success": False, "message": f"API test failed: {response.text}"}
                
    except Exception as e:
        return {"success": False, "message": f"Connection test failed: {str(e)}"}

# WhatsApp Webhook endpoints
@app.get("/webhooks/whatsapp")
async def whatsapp_webhook_verify(request: Request):
    # Get query parameters
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    # Get stored verify token
    settings = await db.whatsapp_settings.find_one({"type": "credentials"})
    stored_token = settings.get("verify_token") if settings else None
    
    # Verify the webhook
    if mode == "subscribe" and token == stored_token:
        print(f"✅ WhatsApp webhook verified successfully")
        return int(challenge)
    else:
        print(f"❌ WhatsApp webhook verification failed")
        print(f"   Mode: {mode}, Token match: {token == stored_token}")
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook_handler(request: Request):
    try:
        # Get the raw body
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        print(f"📨 WhatsApp webhook received: {json.dumps(data, indent=2)}")
        
        # Process webhook data
        if "entry" in data:
            for entry in data["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if change.get("field") == "messages":
                            await process_whatsapp_message(change.get("value", {}))
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"❌ Error processing WhatsApp webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

async def process_whatsapp_message(message_data):
    """Process incoming WhatsApp message and create conversation/message records"""
    try:
        if "messages" not in message_data:
            return
            
        for message in message_data["messages"]:
            wa_id = message.get("from")
            phone_number = f"+{wa_id}"
            message_text = ""
            message_type = "text"
            media_url = None
            
            # Extract message content based on type
            if "text" in message:
                message_text = message["text"]["body"]
            elif "image" in message:
                message_type = "image"
                message_text = message["image"].get("caption", "📷 Image")
                media_url = message["image"].get("link")
            elif "document" in message:
                message_type = "document"
                message_text = f"📄 {message['document'].get('filename', 'Document')}"
                media_url = message["document"].get("link")
            
            # Get or create contact
            contact = await db.contacts.find_one({"wa_id": wa_id})
            if not contact:
                contact = {
                    "_id": f"contact_{uuid.uuid4().hex[:8]}",
                    "id": f"contact_{uuid.uuid4().hex[:8]}",
                    "wa_id": wa_id,
                    "phone": phone_number,
                    "name": f"Contact {wa_id[-4:]}",
                    "tags": ["whatsapp"],
                    "custom_fields": {},
                    "created_at": datetime.now()
                }
                await db.contacts.insert_one(contact)
            
            # Get or create conversation
            conversation = await db.conversations.find_one({
                "contact_id": contact["id"],
                "status": "open"
            })
            
            if not conversation:
                conversation = {
                    "_id": f"conv_{uuid.uuid4().hex[:8]}",
                    "id": f"conv_{uuid.uuid4().hex[:8]}",
                    "contact_id": contact["id"],
                    "department_id": "dept_reception",  # Default to reception
                    "status": "open",
                    "assignee_user_id": None,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "last_message_at": datetime.now(),
                    "sla_due_at": datetime.now() + timedelta(hours=4),
                    "tags": ["whatsapp"]
                }
                await db.conversations.insert_one(conversation)
            
            # Create message record
            new_message = {
                "_id": f"msg_{uuid.uuid4().hex[:8]}",
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "conversation_id": conversation["id"],
                "direction": "in",
                "body": message_text,
                "type": message_type,
                "media_url": media_url,
                "timestamp": datetime.now(),
                "sender_user_id": None,
                "read_status": False,
                "whatsapp_message_id": message.get("id")
            }
            
            await db.messages.insert_one(new_message)
            
            # Update conversation
            await db.conversations.update_one(
                {"id": conversation["id"]},
                {
                    "$set": {
                        "last_message_at": datetime.now(),
                        "updated_at": datetime.now()
                    }
                }
            )
            
            # Broadcast to WebSocket clients
            await manager.broadcast({
                "type": "new_message",
                "conversation_id": conversation["id"],
                "message": clean_document(new_message)
            })
            
            print(f"✅ Processed WhatsApp message from {wa_id}: {message_text[:50]}...")
            
    except Exception as e:
        print(f"❌ Error processing WhatsApp message: {str(e)}")

async def send_whatsapp_message(phone_number: str, message: str):
    """Send message via WhatsApp Cloud API"""
    try:
        settings = await db.whatsapp_settings.find_one({"type": "credentials"})
        if not settings or not settings.get("api_token"):
            raise Exception("WhatsApp credentials not configured")
        
        import httpx
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {settings['api_token']}",
                "Content-Type": "application/json"
            }
            
            # Clean phone number (remove + and formatting)
            clean_phone = phone_number.replace("+", "").replace("-", "").replace(" ", "")
            
            payload = {
                "messaging_product": "whatsapp",
                "to": clean_phone,
                "text": {"body": message}
            }
            
            response = await client.post(
                f"https://graph.facebook.com/v17.0/{settings['phone_number_id']}/messages",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                print(f"✅ WhatsApp message sent to {phone_number}")
                return {"success": True}
            else:
                print(f"❌ Failed to send WhatsApp message: {response.text}")
                return {"success": False, "error": response.text}
                
    except Exception as e:
        print(f"❌ Error sending WhatsApp message: {str(e)}")
        return {"success": False, "error": str(e)}

    return {"success": True}

@app.get("/api/test")
async def test_endpoint():
    try:
        # Test database connection
        count = await db.conversations.count_documents({})
        return {"status": "ok", "conversation_count": count}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "UniWhats Desk API"}