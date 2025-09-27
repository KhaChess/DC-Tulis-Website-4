from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio
from playwright.async_api import async_playwright
import json


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Global storage for active sessions
active_sessions: Dict[str, Dict[str, Any]] = {}

async def discord_automation(session_id: str, session_data: AutoTyperSession):
    """Browser automation for Discord message sending"""
    try:
        logger.info(f"Starting Discord automation for session {session_id}")
        
        async with async_playwright() as p:
            # Launch browser in headless mode
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            # Navigate to Discord
            await page.goto('https://discord.com/channels/@me', wait_until='networkidle')
            
            # Update session status
            active_sessions[session_id]['status'] = 'waiting_for_login'
            await db.auto_typer_sessions.update_one(
                {"id": session_id},
                {"$set": {"status": "waiting_for_login"}}
            )
            
            # Wait for user to login (check for presence of Discord interface)
            login_timeout = 60  # 60 seconds timeout for login
            try:
                # Wait for Discord app to load (look for main navigation or channel list)
                await page.wait_for_selector('[data-list-id="channels"]', timeout=login_timeout * 1000)
                logger.info(f"Discord interface detected for session {session_id}")
            except:
                logger.error(f"Discord login timeout for session {session_id}")
                active_sessions[session_id]['status'] = 'error'
                await db.auto_typer_sessions.update_one(
                    {"id": session_id},
                    {"$set": {"status": "error", "error": "Login timeout"}}
                )
                await browser.close()
                return
            
            # Navigate to the specific channel if it's a valid Discord URL or construct URL
            channel_url = f"https://discord.com/channels/@me/{session_data.channel_id}"
            if session_data.channel_id.startswith('https://discord.com'):
                channel_url = session_data.channel_id
            
            await page.goto(channel_url, wait_until='networkidle')
            
            # Wait for message input to be visible
            await page.wait_for_selector('[data-slate-editor="true"]', timeout=30000)
            
            active_sessions[session_id]['status'] = 'running'
            await db.auto_typer_sessions.update_one(
                {"id": session_id},
                {"$set": {"status": "running"}}
            )
            
            message_index = 0
            while (active_sessions[session_id]['status'] == 'running' and 
                   message_index < len(session_data.messages) * 10):  # Limit iterations
                
                try:
                    message = session_data.messages[message_index % len(session_data.messages)]
                    
                    # Find and click the message input
                    message_input = await page.wait_for_selector('[data-slate-editor="true"]', timeout=10000)
                    await message_input.click()
                    
                    # Type the message with delay
                    await page.keyboard.type(message, delay=session_data.typing_delay // len(message))
                    
                    # Send the message
                    await page.keyboard.press('Enter')
                    
                    # Update success count
                    active_sessions[session_id]['messages_sent'] += 1
                    await db.auto_typer_sessions.update_one(
                        {"id": session_id},
                        {"$set": {"messages_sent": active_sessions[session_id]['messages_sent']}}
                    )
                    
                    logger.info(f"Message sent in session {session_id}: {message[:50]}...")
                    
                    # Wait before next message
                    await asyncio.sleep(session_data.message_delay / 1000)
                    message_index += 1
                    
                except Exception as e:
                    logger.error(f"Error sending message in session {session_id}: {str(e)}")
                    active_sessions[session_id]['messages_failed'] += 1
                    await db.auto_typer_sessions.update_one(
                        {"id": session_id},
                        {"$set": {"messages_failed": active_sessions[session_id]['messages_failed']}}
                    )
                    await asyncio.sleep(2)  # Wait before retry
            
            await browser.close()
            
    except Exception as e:
        logger.error(f"Discord automation error for session {session_id}: {str(e)}")
        if session_id in active_sessions:
            active_sessions[session_id]['status'] = 'error'
        await db.auto_typer_sessions.update_one(
            {"id": session_id},
            {"$set": {"status": "error", "error": str(e)}}
        )


# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class AutoTyperSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    channel_id: str
    messages: List[str]
    typing_delay: int = 1000
    message_delay: int = 5000
    status: str = "idle"  # idle, running, stopped, error
    messages_sent: int = 0
    messages_failed: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class AutoTyperSessionCreate(BaseModel):
    channel_id: str
    messages: List[str]
    typing_delay: int = 1000
    message_delay: int = 5000

class AutoTyperSessionUpdate(BaseModel):
    status: Optional[str] = None
    messages_sent: Optional[int] = None
    messages_failed: Optional[int] = None

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

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
