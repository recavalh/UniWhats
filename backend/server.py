from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
from typing import List, Optional, Dict, Any
import json
from datetime import datetime

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

# Custom JSON encoder for FastAPI responses
from fastapi.encoders import jsonable_encoder

def clean_document(doc):
    """Remove MongoDB ObjectId fields from documents"""
    if doc and isinstance(doc, dict):
        doc.pop('_id', None)
        return doc
    return doc

def clean_documents(docs):
    """Remove MongoDB ObjectId fields from a list of documents"""
    if isinstance(docs, list):
        return [clean_document(doc) for doc in docs]
    return clean_document(docs)
import uuid
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt

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
    conversation_id: str
    body: str
    type: str = "text"

class AssignRequest(BaseModel):
    conversation_id: str
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
    return {"user": user, "token": f"mock_token_{user['id']}"}

@app.get("/api/auth/me")
async def get_current_user(user_id: str = "user_maria"):  # Mock current user
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.pop("password_hash", None)
    return clean_documents(user)

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
    
    return clean_documents(conversations)

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
    current_user_id = "user_maria"
    
    message = {
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
        "message": message
    })
    
    return message

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
    departments = await db.departments.find({"active": True}).to_list(10)
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

@app.get("/api/test")
async def test_endpoint():
    try:
        # Test database connection
        count = await db.conversations.count_documents({})
        return {"status": "ok", "conversation_count": count}
    except Exception as e:
        return {"error": str(e)}