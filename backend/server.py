from fastapi import FastAPI, APIRouter, HTTPException
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Discord automation function will be defined after models


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

# Discord Channel Models
class DiscordChannel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    channel_id: str  # Discord Channel ID
    channel_name: Optional[str] = None
    guild_id: Optional[str] = None
    guild_name: Optional[str] = None
    category: Optional[str] = None  # Custom category set by user
    is_favorite: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
class DiscordChannelCreate(BaseModel):
    channel_id: str
    category: Optional[str] = None
    is_favorite: bool = False

class DiscordChannelUpdate(BaseModel):
    channel_name: Optional[str] = None
    category: Optional[str] = None  
    is_favorite: Optional[bool] = None

# Discord automation function
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

@api_router.post("/auto-typer/start", response_model=AutoTyperSession)
async def start_auto_typer_session(session_create: AutoTyperSessionCreate):
    """Start a new Discord auto-typer session"""
    session = AutoTyperSession(**session_create.dict())
    
    # Store in database
    await db.auto_typer_sessions.insert_one(session.dict())
    
    # Initialize active session
    active_sessions[session.id] = {
        'status': 'starting',
        'messages_sent': 0,
        'messages_failed': 0,
        'task': None
    }
    
    # Start browser automation in background
    task = asyncio.create_task(discord_automation(session.id, session))
    active_sessions[session.id]['task'] = task
    
    logger.info(f"Started auto-typer session {session.id}")
    return session

@api_router.post("/auto-typer/{session_id}/stop")
async def stop_auto_typer_session(session_id: str):
    """Stop an active auto-typer session"""
    if session_id in active_sessions:
        active_sessions[session_id]['status'] = 'stopped'
        
        # Cancel the background task
        if active_sessions[session_id]['task']:
            active_sessions[session_id]['task'].cancel()
        
        # Update database
        await db.auto_typer_sessions.update_one(
            {"id": session_id},
            {"$set": {"status": "stopped"}}
        )
        
        logger.info(f"Stopped auto-typer session {session_id}")
        return {"message": "Session stopped successfully"}
    else:
        return {"error": "Session not found"}

@api_router.get("/auto-typer/{session_id}/status")
async def get_auto_typer_session_status(session_id: str):
    """Get the current status of an auto-typer session"""
    # Get from database
    session_data = await db.auto_typer_sessions.find_one({"id": session_id})
    if not session_data:
        return {"error": "Session not found"}
    
    # Merge with active session data if available
    if session_id in active_sessions:
        session_data['messages_sent'] = active_sessions[session_id]['messages_sent']
        session_data['messages_failed'] = active_sessions[session_id]['messages_failed']
        session_data['status'] = active_sessions[session_id]['status']
    
    return session_data

@api_router.get("/auto-typer/sessions", response_model=List[AutoTyperSession])
async def get_auto_typer_sessions():
    """Get all auto-typer sessions"""
    sessions = await db.auto_typer_sessions.find().sort("created_at", -1).limit(50).to_list(50)
    
    # Update with active session data
    for session in sessions:
        if session['id'] in active_sessions:
            session['messages_sent'] = active_sessions[session['id']]['messages_sent']
            session['messages_failed'] = active_sessions[session['id']]['messages_failed']
            session['status'] = active_sessions[session['id']]['status']
    
    return [AutoTyperSession(**session) for session in sessions]

# Discord Channel Management API Endpoints
@api_router.post("/channels", response_model=DiscordChannel)
async def create_discord_channel(channel_create: DiscordChannelCreate):
    """Add a new Discord channel to saved list"""
    try:
        # Check if channel already exists
        existing = await db.discord_channels.find_one({"channel_id": channel_create.channel_id})
        if existing:
            raise HTTPException(status_code=400, detail="Channel already exists in saved list")
        
        # Create new channel record
        channel = DiscordChannel(**channel_create.dict())
        
        # Try to fetch channel info from Discord API if token is available
        discord_token = os.environ.get('DISCORD_BOT_TOKEN')
        if discord_token:
            try:
                channel_info = await fetch_discord_channel_info(channel_create.channel_id, discord_token)
                if channel_info:
                    channel.channel_name = channel_info.get('name')
                    channel.guild_id = channel_info.get('guild_id') 
                    channel.guild_name = channel_info.get('guild_name')
            except Exception as e:
                logger.warning(f"Could not fetch Discord channel info: {str(e)}")
        
        # Save to database
        await db.discord_channels.insert_one(channel.dict())
        logger.info(f"Added Discord channel {channel.channel_id}")
        return channel
        
    except Exception as e:
        logger.error(f"Error creating Discord channel: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/channels", response_model=List[DiscordChannel])
async def get_discord_channels(search: Optional[str] = None, category: Optional[str] = None, favorites_only: bool = False):
    """Get all saved Discord channels with optional filtering"""
    try:
        # Build query
        query = {}
        if favorites_only:
            query["is_favorite"] = True
        if category:
            query["category"] = category
            
        channels = await db.discord_channels.find(query).sort("created_at", -1).to_list(1000)
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            channels = [
                channel for channel in channels 
                if (search_lower in (channel.get('channel_name') or '').lower() or
                    search_lower in (channel.get('guild_name') or '').lower() or  
                    search_lower in (channel.get('category') or '').lower() or
                    search_lower in (channel.get('channel_id') or '').lower())
            ]
        
        return [DiscordChannel(**channel) for channel in channels]
        
    except Exception as e:
        logger.error(f"Error fetching Discord channels: {str(e)}")
        return []

@api_router.put("/channels/{channel_id}", response_model=DiscordChannel)
async def update_discord_channel(channel_id: str, channel_update: DiscordChannelUpdate):
    """Update a saved Discord channel"""
    try:
        # Find existing channel
        existing = await db.discord_channels.find_one({"id": channel_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        # Prepare update data
        update_data = channel_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Update in database
        await db.discord_channels.update_one(
            {"id": channel_id},
            {"$set": update_data}
        )
        
        # Return updated channel
        updated_channel = await db.discord_channels.find_one({"id": channel_id})
        return DiscordChannel(**updated_channel)
        
    except Exception as e:
        logger.error(f"Error updating Discord channel: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/channels/{channel_id}")
async def delete_discord_channel(channel_id: str):
    """Delete a saved Discord channel"""
    try:
        result = await db.discord_channels.delete_one({"id": channel_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        logger.info(f"Deleted Discord channel {channel_id}")
        return {"message": "Channel deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting Discord channel: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/channels/categories")
async def get_channel_categories():
    """Get all unique categories used by saved channels"""
    try:
        categories = await db.discord_channels.distinct("category")
        # Filter out None/empty categories  
        categories = [cat for cat in categories if cat and cat.strip()]
        return {"categories": sorted(categories)}
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return {"categories": []}

# Helper function to fetch Discord channel info
async def fetch_discord_channel_info(channel_id: str, bot_token: str):
    """Fetch channel information from Discord API"""
    try:
        import aiohttp
        
        headers = {
            'Authorization': f'Bot {bot_token}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            # Get channel info
            async with session.get(
                f'https://discord.com/api/v10/channels/{channel_id}',
                headers=headers
            ) as response:
                if response.status == 200:
                    channel_data = await response.json()
                    
                    result = {
                        'name': channel_data.get('name'),
                        'guild_id': channel_data.get('guild_id')
                    }
                    
                    # Get guild info if guild_id exists
                    if result['guild_id']:
                        async with session.get(
                            f'https://discord.com/api/v10/guilds/{result["guild_id"]}',
                            headers=headers
                        ) as guild_response:
                            if guild_response.status == 200:
                                guild_data = await guild_response.json()
                                result['guild_name'] = guild_data.get('name')
                    
                    return result
                else:
                    logger.warning(f"Discord API error {response.status} for channel {channel_id}")
                    return None
                    
    except Exception as e:
        logger.error(f"Error fetching Discord channel info: {str(e)}")
        return None

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
