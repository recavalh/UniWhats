from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Request, UploadFile, File, Form
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
from bson import ObjectId
import bcrypt
import base64

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data
def clean_document(doc: dict) -> dict:
    """Clean MongoDB document for JSON serialization - convert datetime objects and ObjectIds"""
    if doc is None:
        return None
    
    cleaned = {}
    for key, value in doc.items():
        if key == '_id':
            # Skip MongoDB's internal _id field
            continue
        elif isinstance(value, datetime):
            cleaned[key] = value.isoformat()
        elif isinstance(value, ObjectId):
            # Convert ObjectId to string
            cleaned[key] = str(value)
        elif isinstance(value, list):
            cleaned[key] = [clean_document(item) if isinstance(item, dict) else (str(item) if isinstance(item, ObjectId) else item) for item in value]
        elif isinstance(value, dict):
            cleaned[key] = clean_document(value)
        else:
            cleaned[key] = value
    return cleaned

# MongoDB Connection
print(f"🔍 Debug: All environment variables: {list(os.environ.keys())}")
print(f"🔍 Debug: MONGO_URL from env: {os.environ.get('MONGO_URL')}")

MONGO_URL = os.environ.get('MONGO_URL')
if not MONGO_URL:
    # Try to load from .env file manually
    try:
        from dotenv import load_dotenv
        load_dotenv('/app/backend/.env')
        MONGO_URL = os.environ.get('MONGO_URL')
        print(f"🔍 Debug: MONGO_URL after loading .env: {MONGO_URL}")
    except ImportError:
        pass
    
    if not MONGO_URL:
        MONGO_URL = "mongodb://localhost:27017"  # Default fallback
        print(f"🔍 Debug: Using fallback MONGO_URL: {MONGO_URL}")

print(f"🔗 Connecting to MongoDB: {MONGO_URL}")

client = AsyncIOMotorClient(MONGO_URL)
db = client.uniwhats_db

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: dict):
        message_text = json.dumps(message, default=str)
        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            await manager.broadcast(message_data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Dependency to get current user
def get_current_user_from_token(authorization: str) -> Optional[str]:
    """Extract user ID from token"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    if token.startswith("uniwhats_"):
        try:
            # Extract user ID from token format: uniwhats_user_admin_random
            parts = token.split("_")
            if len(parts) >= 4:
                # Reconstruct user_id from parts 1 and 2: user_admin, user_maria, etc.
                user_id = f"{parts[1]}_{parts[2]}"
                return user_id
        except Exception as e:
            print(f"❌ Token parsing error: {e}")
    return None

async def get_current_user(request: Request) -> dict:
    """Get current user from token"""
    authorization = request.headers.get("authorization") or request.headers.get("Authorization")
    user_id = get_current_user_from_token(authorization)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get user from database
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

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
    assigned_user_id: Optional[str] = None
    last_message_at: datetime
    status: str  # 'open', 'closed', 'assigned'
    tags: List[str] = []
    created_at: datetime

class LoginRequest(BaseModel):
    email: str
    password: str

class WhatsAppSettings(BaseModel):
    phone_number_id: str = ""
    business_account_id: str = ""
    api_token: str = ""
    webhook_verify_token: str = ""
    webhook_url: str

class TagRequest(BaseModel):
    tags: List[str]

# Add initial mock data
async def initialize_mock_data():
    # Check if data already exists
    existing_users = await db.users.count_documents({})
    if existing_users > 0:
        print("✅ Mock data already exists, skipping initialization")
        return

    print("🔄 Initializing mock data...")
    
    # Departments
    departments = [
        {
            "id": "dept_reception",
            "name": "Reception & Finance",
            "description": "Recepção e questões financeiras",
            "business_hours": {"monday": "8:00-17:00", "tuesday": "8:00-17:00"},
            "active": True
        },
        {
            "id": "dept_coordination",
            "name": "Coordination",
            "description": "Coordenação pedagógica",
            "business_hours": {"monday": "8:00-17:00", "tuesday": "8:00-17:00"},
            "active": True
        },
        {
            "id": "dept_sales",
            "name": "Sales",
            "description": "Vendas e prospecção",
            "business_hours": {"monday": "8:00-17:00", "tuesday": "8:00-17:00"},
            "active": True
        },
        {
            "id": "dept_management",
            "name": "Management",
            "description": "Direção e administração",
            "business_hours": {"monday": "8:00-17:00", "tuesday": "8:00-17:00"},
            "active": True
        }
    ]
    await db.departments.insert_many(departments)

    # Users
    users = [
        {
            "id": "user_admin",
            "name": "João Diretor",
            "email": "admin@school.com",
            "password_hash": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "Manager",
            "department_id": "dept_management",
            "avatar": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face"
        },
        {
            "id": "user_maria",
            "name": "Maria Silva",
            "email": "maria@school.com",
            "password_hash": bcrypt.hashpw("maria123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "Receptionist",
            "department_id": "dept_reception",
            "avatar": "https://images.unsplash.com/photo-1494790108755-2616b7b6ca85?w=150&h=150&fit=crop&crop=face"
        },
        {
            "id": "user_carlos",
            "name": "Carlos Souza",
            "email": "carlos@school.com",
            "password_hash": bcrypt.hashpw("carlos123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "Coordinator",
            "department_id": "dept_coordination",
            "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face"
        },
        {
            "id": "user_ana",
            "name": "Ana Costa",
            "email": "ana@school.com",
            "password_hash": bcrypt.hashpw("ana123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "role": "Sales Rep",
            "department_id": "dept_sales",
            "avatar": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face"
        }
    ]
    await db.users.insert_many(users)

    # Contacts
    contacts = [
        {
            "id": "contact_roberto",
            "wa_id": "5511876543210",
            "phone": "+55 11 87654-3210",
            "name": "Roberto Fernandes",
            "student_id": "STU002",
            "tags": ["parent", "grade8"],
            "custom_fields": {"student_name": "Sofia Fernandes", "grade": "8º Ano"},
            "created_at": datetime.now() - timedelta(days=7)
        },
        {
            "id": "contact_amanda",
            "wa_id": "5511987654321",
            "phone": "+55 11 98765-4321",
            "name": "Amanda Silva",
            "student_id": None,
            "tags": ["lead", "hot"],
            "custom_fields": {"interest": "Ensino Médio"},
            "created_at": datetime.now() - timedelta(days=3)
        },
        {
            "id": "contact_patricia",
            "wa_id": "5511876543218",
            "phone": "+55 11 87654-3218",
            "name": "Patricia Almeida",
            "student_id": "STU003",
            "tags": ["cancellation", "urgent"],
            "custom_fields": {"reason": "Mudança de cidade"},
            "created_at": datetime.now() - timedelta(days=1)
        }
    ]
    await db.contacts.insert_many(contacts)

    # Conversations
    conversations = [
        {
            "id": "conv_roberto",
            "contact_id": "contact_roberto",
            "department_id": "dept_reception",
            "assigned_user_id": "user_maria",
            "last_message_at": datetime.now() - timedelta(minutes=30),
            "status": "open",
            "tags": ["payment"],
            "created_at": datetime.now() - timedelta(days=7)
        },
        {
            "id": "conv_amanda",
            "contact_id": "contact_amanda",
            "department_id": "dept_sales",
            "assigned_user_id": "user_ana",
            "last_message_at": datetime.now() - timedelta(hours=2),
            "status": "open",
            "tags": ["lead", "hot"],
            "created_at": datetime.now() - timedelta(days=3)
        },
        {
            "id": "conv_patricia",
            "contact_id": "contact_patricia",  
            "department_id": "dept_coordination",
            "assigned_user_id": "user_carlos",
            "last_message_at": datetime.now() - timedelta(hours=5),
            "status": "open",
            "tags": ["cancellation", "urgent"],
            "created_at": datetime.now() - timedelta(days=1)
        }
    ]
    await db.conversations.insert_many(conversations)

    # Messages
    messages = [
        {
            "id": "msg_1",
            "conversation_id": "conv_roberto",
            "direction": "in",
            "body": "Bom dia! Recebi uma cobrança diferente este mês. Podem me explicar o que aconteceu?",
            "type": "text",
            "timestamp": datetime.now() - timedelta(hours=1),
            "sender_user_id": None,
            "read_status": True
        },
        {
            "id": "msg_2",
            "conversation_id": "conv_roberto",
            "direction": "in",
            "body": "Segue a foto da fatura que recebi",
            "type": "image",
            "media_url": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=400&h=300&fit=crop",
            "timestamp": datetime.now() - timedelta(minutes=5),
            "sender_user_id": None,
            "read_status": False
        },
        {
            "id": "msg_3",
            "conversation_id": "conv_amanda",
            "direction": "in",
            "body": "Olá Amanda! Que bom saber do seu interesse na nossa escola. Você poderia me contar um pouco mais sobre o que procura?",
            "type": "text",
            "timestamp": datetime.now() - timedelta(hours=2),
            "sender_user_id": "user_ana",
            "read_status": True
        },
        {
            "id": "msg_4",
            "conversation_id": "conv_patricia",
            "direction": "in",
            "body": "Olá Patricia! Entendo sua situação. Podemos conversar sobre as opções disponíveis para o seu caso?",
            "type": "text",
            "timestamp": datetime.now() - timedelta(hours=5),
            "sender_user_id": "user_carlos",
            "read_status": True
        }
    ]
    await db.messages.insert_many(messages)

    # WhatsApp Settings (empty by default)
    whatsapp_settings = {
        "id": "whatsapp_settings",
        "phone_number_id": "",
        "business_account_id": "",
        "api_token": "",
        "webhook_verify_token": "",
        "webhook_url": "",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    await db.whatsapp_settings.insert_one(whatsapp_settings)

    print("✅ Mock data initialized successfully")

@app.on_event("startup")
async def startup_event():
    await initialize_mock_data()

# API Routes

@app.get("/")
async def root():
    return {"message": "UniWhats Desk API is running"}

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    # Find user by email
    user = await db.users.find_one({"email": request.email})
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check password
    if not bcrypt.checkpw(request.password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token = f"uniwhats_{user['id']}_{uuid.uuid4().hex[:8]}"
    
    # Remove password from response
    user.pop('password_hash', None)
    
    return {
        "token": token,
        "user": clean_document(user)
    }

@app.post("/api/auth/forgot-password")
async def forgot_password(request: dict):
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Mock response - in production, send actual email
    return {"message": "If this email exists, you will receive password reset instructions."}

# FIXED: Updated access control rules based on requirements
@app.get("/api/conversations")
async def get_conversations(request: Request):
    current_user = await get_current_user(request)
    
    # Build query based on user role
    query = {}
    
    if current_user['role'] == "Manager":
        # Managers can see all conversations
        pass
    elif current_user['role'] == "Receptionist":
        # Receptionists see new messages (status='open' and unassigned) and messages assigned to them
        query = {
            "$or": [
                {"status": "open", "assigned_user_id": None},  # New/unassigned messages
                {"assigned_user_id": current_user["id"]}       # Messages assigned to them
            ]
        }
    else:
        # Other roles only see conversations assigned to their department or to them
        query = {
            "$or": [
                {"department_id": current_user.get("department_id")},
                {"assigned_user_id": current_user["id"]}
            ]
        }
    
    conversations = await db.conversations.find(query).sort("last_message_at", -1).to_list(100)
    
    # Enrich with contact data
    enriched_conversations = []
    for conv in conversations:
        contact = await db.contacts.find_one({"id": conv["contact_id"]})
        if contact:
            conv["contact"] = clean_document(contact)
        
        # Get last message
        last_message = await db.messages.find_one(
            {"conversation_id": conv["id"]},
            sort=[("timestamp", -1)]
        )
        if last_message:
            conv["last_message"] = clean_document(last_message)
            
        enriched_conversations.append(clean_document(conv))
    
    return enriched_conversations

@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, request: Request):
    current_user = await get_current_user(request)
    
    # Check if user has access to this conversation
    conversation = await db.conversations.find_one({"id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check access permissions
    has_access = False
    if current_user['role'] in ["Manager", "Receptionist"]:
        has_access = True
    elif (conversation.get("department_id") == current_user.get("department_id") or 
          conversation.get("assigned_user_id") == current_user["id"]):
        has_access = True
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied to this conversation")
    
    messages = await db.messages.find({"conversation_id": conversation_id}).sort("timestamp", 1).to_list(100)
    
    # Enrich with sender data
    enriched_messages = []
    for message in messages:
        if message.get("sender_user_id"):
            sender = await db.users.find_one({"id": message["sender_user_id"]})
            if sender:
                sender.pop('password_hash', None)
                message["sender"] = clean_document(sender)
        enriched_messages.append(clean_document(message))
    
    return enriched_messages

@app.post("/api/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, message_data: dict, request: Request):
    current_user = await get_current_user(request)
    
    # Check conversation access
    conversation = await db.conversations.find_one({"id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    has_access = False
    if current_user['role'] in ["Manager", "Receptionist"]:
        has_access = True
    elif (conversation.get("department_id") == current_user.get("department_id") or 
          conversation.get("assigned_user_id") == current_user["id"]):
        has_access = True
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied to this conversation")
    
    message = {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "conversation_id": conversation_id,
        "direction": "out",
        "body": message_data.get("body", ""),
        "type": message_data.get("type", "text"),
        "timestamp": datetime.now(),
        "sender_user_id": current_user["id"],
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
    
    await manager.broadcast({
        "type": "conversation_updated", 
        "conversation_id": conversation_id
    })
    
    return clean_document(message)

@app.post("/api/conversations/{conversation_id}/messages/media")
async def send_media_message(
    conversation_id: str,
    file: UploadFile = File(...),
    body: str = Form(""),
    type: str = Form("image"),
    request: Request = None
):
    current_user = await get_current_user(request)
    
    # Check conversation access
    conversation = await db.conversations.find_one({"id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    has_access = False
    if current_user['role'] in ["Manager", "Receptionist"]:
        has_access = True
    elif (conversation.get("department_id") == current_user.get("department_id") or 
          conversation.get("assigned_user_id") == current_user["id"]):
        has_access = True
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied to this conversation")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Convert to base64 for storage
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Determine media type
        media_type = type
        if media_type not in ['image', 'document', 'audio']:
            media_type = 'document'
        
        # Create message with media
        message = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "conversation_id": conversation_id,
            "direction": "out",
            "body": body or f"📎 {file.filename}",
            "type": media_type,
            "timestamp": datetime.now(),
            "sender_user_id": current_user["id"],
            "read_status": True,
            "media": {
                "filename": file.filename,
                "content_type": file.content_type,
                "data": file_base64,
                "size": len(file_content)
            }
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
        
        return clean_document(message)
        
    except Exception as e:
        print(f"Error uploading media: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload media: {str(e)}")

@app.post("/api/conversations/{conversation_id}/assign")
async def assign_conversation(conversation_id: str, assignment_data: dict, request: Request):
    current_user = await get_current_user(request)
    
    # Only managers and receptionists can assign conversations
    if current_user['role'] not in ["Manager", "Receptionist"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    user_id = assignment_data.get("user_id")
    department_id = assignment_data.get("department_id")
    
    update_data = {"updated_at": datetime.now()}
    if user_id:
        update_data["assigned_user_id"] = user_id
    if department_id:
        update_data["department_id"] = department_id
    
    result = await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await manager.broadcast({
        "type": "conversation_assigned",
        "conversation_id": conversation_id,
        "assigned_user_id": user_id,
        "department_id": department_id
    })
    
    return {"message": "Conversation assigned successfully"}

@app.post("/api/conversations/{conversation_id}/mark-read")
async def mark_conversation_read(conversation_id: str, request: Request):
    current_user = await get_current_user(request)
    
    # Check conversation access
    conversation = await db.conversations.find_one({"id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    has_access = False
    if current_user['role'] in ["Manager", "Receptionist"]:
        has_access = True
    elif (conversation.get("department_id") == current_user.get("department_id") or 
          conversation.get("assigned_user_id") == current_user["id"]):
        has_access = True
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied to this conversation")
    
    # Mark all messages in this conversation as read
    await db.messages.update_many(
        {"conversation_id": conversation_id, "direction": "in"},
        {"$set": {"read_status": True}}
    )
    
    return {"message": "Messages marked as read"}

# NEW: Add/Remove tags from conversations
@app.post("/api/conversations/{conversation_id}/tags")
async def update_conversation_tags(conversation_id: str, tag_request: TagRequest, request: Request):
    current_user = await get_current_user(request)
    
    # Check conversation access
    conversation = await db.conversations.find_one({"id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    has_access = False
    if current_user['role'] in ["Manager", "Receptionist"]:
        has_access = True
    elif (conversation.get("department_id") == current_user.get("department_id") or 
          conversation.get("assigned_user_id") == current_user["id"]):
        has_access = True
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied to this conversation")
    
    # Update tags
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"tags": tag_request.tags, "updated_at": datetime.now()}}
    )
    
    await manager.broadcast({
        "type": "conversation_tags_updated",
        "conversation_id": conversation_id,
        "tags": tag_request.tags
    })
    
    return {"message": "Tags updated successfully", "tags": tag_request.tags}

# NEW: Close conversation endpoint
@app.post("/api/conversations/{conversation_id}/close")
async def close_conversation(conversation_id: str, request: Request):
    current_user = await get_current_user(request)
    
    # Check conversation access
    conversation = await db.conversations.find_one({"id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    has_access = False
    if current_user['role'] in ["Manager", "Receptionist"]:
        has_access = True
    elif (conversation.get("department_id") == current_user.get("department_id") or 
          conversation.get("assigned_user_id") == current_user["id"]):
        has_access = True
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied to this conversation")
    
    # Update conversation status to closed
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"status": "closed", "updated_at": datetime.now()}}
    )
    
    # Add a system message indicating the conversation was closed
    close_message = {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "conversation_id": conversation_id,
        "direction": "system",
        "body": f"Conversa fechada por {current_user['name']}",
        "type": "system",
        "timestamp": datetime.now(),
        "sender_user_id": current_user["id"],
        "read_status": True
    }
    
    await db.messages.insert_one(close_message)
    
    await manager.broadcast({
        "type": "conversation_closed",
        "conversation_id": conversation_id,
        "closed_by": current_user["name"]
    })
    
    return {"message": "Conversation closed successfully", "status": "closed"}

# NEW: Reopen conversation endpoint
@app.post("/api/conversations/{conversation_id}/reopen")
async def reopen_conversation(conversation_id: str, request: Request):
    current_user = await get_current_user(request)
    
    # Check conversation access
    conversation = await db.conversations.find_one({"id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    has_access = False
    if current_user['role'] in ["Manager", "Receptionist"]:
        has_access = True
    elif (conversation.get("department_id") == current_user.get("department_id") or 
          conversation.get("assigned_user_id") == current_user["id"]):
        has_access = True
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied to this conversation")
    
    # Update conversation status to open
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"status": "open", "updated_at": datetime.now()}}
    )
    
    # Add a system message indicating the conversation was reopened
    reopen_message = {
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "conversation_id": conversation_id,
        "direction": "system",
        "body": f"Conversa reaberta por {current_user['name']}",
        "type": "system",
        "timestamp": datetime.now(),
        "sender_user_id": current_user["id"],
        "read_status": True
    }
    
    await db.messages.insert_one(reopen_message)
    
    await manager.broadcast({
        "type": "conversation_reopened",
        "conversation_id": conversation_id,
        "reopened_by": current_user["name"]
    })
    
    return {"message": "Conversation reopened successfully", "status": "open"}

@app.put("/api/users/profile")
async def update_my_profile(profile_data: dict, request: Request):
    # Extract current user from token
    authorization = request.headers.get("authorization") or request.headers.get("Authorization")
    current_user_id = None
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        if token.startswith("uniwhats_"):
            try:
                # Extract user ID from token format: uniwhats_user_admin_random
                parts = token.split("_")
                if len(parts) >= 4:
                    # Reconstruct user_id from parts 1 and 2: user_admin, user_maria, etc.
                    current_user_id = f"{parts[1]}_{parts[2]}"
                    print(f"✅ Profile update - extracted user_id: {current_user_id}")
                else:
                    print(f"❌ Profile update - invalid token format: {token}")
            except Exception as e:
                print(f"❌ Profile update - token parsing error: {e}")
    
    if not current_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check if user exists
    current_user = await db.users.find_one({"id": current_user_id})
    if not current_user:
        print(f"❌ Profile update - user not found for ID: {current_user_id}")
        raise HTTPException(status_code=401, detail="User not found")
    
    print(f"✅ Profile update request: {profile_data}")
    
    # Update user profile
    update_data = {}
    if "name" in profile_data and profile_data["name"].strip():
        update_data["name"] = profile_data["name"].strip()
        print(f"✅ Updating name to: {update_data['name']}")
    if "email" in profile_data and profile_data["email"].strip():
        # Check if email is already taken by another user
        existing_user = await db.users.find_one({"email": profile_data["email"], "id": {"$ne": current_user_id}})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        update_data["email"] = profile_data["email"].strip()
    if "avatar" in profile_data:
        update_data["avatar"] = profile_data["avatar"]
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    update_data["updated_at"] = datetime.now()
    
    print(f"✅ Executing database update: {update_data}")
    
    result = await db.users.update_one(
        {"id": current_user_id},
        {"$set": update_data}
    )
    
    print(f"✅ Database update result: matched={result.matched_count}, modified={result.modified_count}")
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return updated user data
    updated_user = await db.users.find_one({"id": current_user_id})
    updated_user.pop("password_hash", None)
    
    print(f"✅ Profile updated successfully: {updated_user.get('name')}")
    
    return clean_document(updated_user)

@app.put("/api/users/{user_id}/profile")
async def update_user_profile(user_id: str, profile_data: dict, request: Request):
    current_user = await get_current_user(request)
    
    # Check if current user can update this profile
    if current_user["id"] != user_id and current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if target user exists
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
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

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, request: Request):
    current_user = await get_current_user(request)
    
    conversation = await db.conversations.find_one({"id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check access permissions
    has_access = False
    if current_user['role'] in ["Manager", "Receptionist"]:
        has_access = True
    elif (conversation.get("department_id") == current_user.get("department_id") or 
          conversation.get("assigned_user_id") == current_user["id"]):
        has_access = True
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied to this conversation")
    
    # Enrich with contact data
    contact = await db.contacts.find_one({"id": conversation["contact_id"]})
    if contact:
        conversation["contact"] = clean_document(contact)
    
    return clean_document(conversation)

# Admin endpoints (existing...)
@app.get("/api/admin/users")
async def get_users(request: Request):
    current_user = await get_current_user(request)
    
    if current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    users = await db.users.find({}).to_list(100)
    # Remove password hashes
    for user in users:
        user.pop('password_hash', None)
    
    return [clean_document(user) for user in users]

@app.post("/api/admin/users")
async def create_user(user_data: dict, request: Request):
    current_user = await get_current_user(request)
    
    if current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data["email"]})
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already exists")
    
    # Hash password
    password_hash = bcrypt.hashpw(user_data["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    new_user = {
        "id": f"user_{uuid.uuid4().hex[:8]}",
        "name": user_data["name"],
        "email": user_data["email"],
        "password_hash": password_hash,
        "role": user_data["role"],
        "department_id": user_data.get("department_id"),
        "avatar": user_data.get("avatar", ""),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    await db.users.insert_one(new_user)
    
    # Remove password hash from response
    new_user.pop('password_hash', None)
    
    return clean_document(new_user)

@app.put("/api/admin/users/{user_id}")
async def update_user(user_id: str, user_data: dict, request: Request):
    current_user = await get_current_user(request)
    
    if current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {
        "name": user_data["name"],
        "email": user_data["email"],
        "role": user_data["role"],
        "department_id": user_data.get("department_id"),
        "avatar": user_data.get("avatar", ""),
        "updated_at": datetime.now()
    }
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = await db.users.find_one({"id": user_id})
    updated_user.pop('password_hash', None)
    
    return clean_document(updated_user)

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: str, request: Request):
    current_user = await get_current_user(request)
    
    if current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Don't allow deleting self
    if current_user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    result = await db.users.delete_one({"id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

@app.post("/api/admin/users/{user_id}/reset-password")
async def reset_user_password(user_id: str, request: Request):
    current_user = await get_current_user(request)
    
    if current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Generate temporary password
    temp_password = f"temp{uuid.uuid4().hex[:6]}"
    password_hash = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"password_hash": password_hash, "updated_at": datetime.now()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Password reset successfully", "temporary_password": temp_password}

@app.get("/api/admin/departments")
async def get_departments(request: Request):
    current_user = await get_current_user(request)
    
    if current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    departments = await db.departments.find({}).to_list(100)
    return [clean_document(dept) for dept in departments]

@app.post("/api/admin/departments")
async def create_department(dept_data: dict, request: Request):
    current_user = await get_current_user(request)
    
    if current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    new_dept = {
        "id": f"dept_{uuid.uuid4().hex[:8]}",
        "name": dept_data["name"],
        "description": dept_data["description"],
        "business_hours": dept_data.get("business_hours", {}),
        "active": dept_data.get("active", True),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    await db.departments.insert_one(new_dept)
    return clean_document(new_dept)

@app.put("/api/admin/departments/{dept_id}")
async def update_department(dept_id: str, dept_data: dict, request: Request):
    current_user = await get_current_user(request)
    
    if current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    update_data = {
        "name": dept_data["name"],
        "description": dept_data["description"],
        "business_hours": dept_data.get("business_hours", {}),
        "active": dept_data.get("active", True),
        "updated_at": datetime.now()
    }
    
    result = await db.departments.update_one(
        {"id": dept_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")
    
    updated_dept = await db.departments.find_one({"id": dept_id})
    return clean_document(updated_dept)

@app.delete("/api/admin/departments/{dept_id}")
async def delete_department(dept_id: str, request: Request):
    current_user = await get_current_user(request)
    
    if current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.departments.delete_one({"id": dept_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")
    
    return {"message": "Department deleted successfully"}

@app.post("/api/admin/departments/{dept_id}/toggle")
async def toggle_department(dept_id: str, request: Request):
    current_user = await get_current_user(request)
    
    if current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get current state
    dept = await db.departments.find_one({"id": dept_id})
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Toggle active state
    new_active_state = not dept.get("active", True)
    
    result = await db.departments.update_one(
        {"id": dept_id},
        {"$set": {"active": new_active_state, "updated_at": datetime.now()}}
    )
    
    return {"message": f"Department {'activated' if new_active_state else 'deactivated'}", "active": new_active_state}

# WhatsApp Settings
@app.get("/api/admin/whatsapp/settings")
async def get_whatsapp_settings(request: Request):
    current_user = await get_current_user(request)
    
    if current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    settings = await db.whatsapp_settings.find_one({"id": "whatsapp_settings"})
    if not settings:
        # Return empty settings if none exist
        settings = {
            "phone_number_id": "",
            "business_account_id": "",
            "api_token": "",
            "webhook_verify_token": "",
            "webhook_url": ""
        }
    
    return clean_document(settings)

@app.post("/api/admin/whatsapp/settings")
async def update_whatsapp_settings(settings_data: WhatsAppSettings, request: Request):
    current_user = await get_current_user(request)
    
    if current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    settings = {
        "id": "whatsapp_settings",
        "phone_number_id": settings_data.phone_number_id,
        "business_account_id": settings_data.business_account_id,
        "api_token": settings_data.api_token,
        "webhook_verify_token": settings_data.webhook_verify_token,
        "webhook_url": settings_data.webhook_url,
        "updated_at": datetime.now()
    }
    
    await db.whatsapp_settings.update_one(
        {"id": "whatsapp_settings"},
        {"$set": settings},
        upsert=True
    )
    
    return {"message": "WhatsApp settings updated successfully"}

@app.post("/api/admin/whatsapp/test-connection")
async def test_whatsapp_connection(request: Request):
    current_user = await get_current_user(request)
    
    if current_user["role"] not in ["Manager"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Mock test - in production, make actual API call
    return {"message": "Connection test successful", "status": "connected"}

# WhatsApp Webhooks
@app.get("/webhooks/whatsapp")
async def verify_webhook(request: Request):
    # WhatsApp webhook verification
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    # Get webhook settings
    settings = await db.whatsapp_settings.find_one({"id": "whatsapp_settings"})
    expected_token = settings.get("webhook_verify_token", "") if settings else ""
    
    if mode == "subscribe" and token == expected_token and expected_token:
        return int(challenge)
    else:
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request):
    # Handle incoming WhatsApp messages
    body = await request.json()
    
    # Process webhook data (simplified)  
    if body.get("object") == "whatsapp_business_account":
        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                if change.get("field") == "messages":
                    messages = change.get("value", {}).get("messages", [])
                    for message in messages:
                        # Process incoming message
                        await process_incoming_message(message)
    
    return {"status": "ok"}

async def process_incoming_message(message_data: dict):
    """Process incoming WhatsApp message"""
    # This would contain the logic to:
    # 1. Find or create contact
    # 2. Find or create conversation  
    # 3. Save the message
    # 4. Route to appropriate department
    # 5. Broadcast via WebSocket
    
    # For now, just log
    print(f"📨 Received WhatsApp message: {message_data}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)