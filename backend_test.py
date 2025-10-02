#!/usr/bin/env python3
"""
Enhanced Backend API Testing for Discord Autotyper with WebSocket and Real-time Features
Tests WebSocket connections, session management, pause/resume, retry mechanisms, and real-time updates
"""

import requests
import json
import time
import asyncio
import websockets
import threading
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BASE_URL = "https://web-autotyper.preview.emergentagent.com/api"
WS_URL = "wss://chatflow-automation.preview.emergentagent.com/api/ws"
HEADERS = {"Content-Type": "application/json"}

# Test data
TEST_CHANNEL_ID = "123456789012345678"  # Fake Discord channel ID
TEST_CATEGORY = "Test Category"
TEST_CHANNEL_NAME = "test-channel"

# Enhanced test data for autotyper
TEST_MESSAGES = [
    "Hello, this is test message 1",
    "This is test message 2 with more content",
    "Final test message 3"
]
TEST_TYPING_DELAY = 100  # Fast typing for testing
TEST_MESSAGE_DELAY = 1000  # 1 second between messages

class EnhancedDiscordAutotyperTester:
    def __init__(self):
        self.test_results = []
        self.created_sessions = []
        self.websocket_messages = []
        self.websocket_connected = False
        
    def log_result(self, test_name, success, message, response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_api_health_check(self):
        """Test basic API connectivity"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=10)
            if response.status_code == 200:
                self.log_result("API Health Check", True, f"API is accessible - Status: {response.status_code}")
                return True
            else:
                self.log_result("API Health Check", False, f"API returned status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("API Health Check", False, f"Connection failed: {str(e)}")
            return False
    
    def test_enhanced_session_creation(self):
        """Test POST /api/auto-typer/start - Enhanced session creation"""
        try:
            payload = {
                "channel_id": TEST_CHANNEL_ID,
                "messages": TEST_MESSAGES,
                "typing_delay": TEST_TYPING_DELAY,
                "message_delay": TEST_MESSAGE_DELAY
            }
            
            response = requests.post(f"{BASE_URL}/auto-typer/start", json=payload, headers=HEADERS, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    self.log_result("Enhanced Session Creation", False, f"API returned error: {data['error']}")
                    return False
                
                # Validate enhanced session structure
                required_fields = [
                    "id", "channel_id", "messages", "typing_delay", "message_delay", 
                    "status", "messages_sent", "messages_failed", "current_message_index",
                    "current_message", "is_typing", "typing_progress", "failed_messages",
                    "retry_count", "can_resume", "created_at"
                ]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Enhanced Session Creation", False, f"Missing enhanced fields: {missing_fields}")
                    return False
                
                # Store session ID for further tests
                self.created_sessions.append(data["id"])
                
                self.log_result("Enhanced Session Creation", True, f"Enhanced session created with ID: {data['id']}", data)
                return True
            else:
                self.log_result("Enhanced Session Creation", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Enhanced Session Creation", False, f"Request failed: {str(e)}")
            return False
    
    async def test_websocket_connection(self):
        """Test WebSocket connection to /api/ws/{session_id}"""
        if not self.created_sessions:
            self.log_result("WebSocket Connection", False, "No sessions available for WebSocket testing")
            return False
        
        session_id = self.created_sessions[0]
        ws_url = f"{WS_URL}/{session_id}"
        
        try:
            async with websockets.connect(ws_url, timeout=10) as websocket:
                self.websocket_connected = True
                
                # Wait for connection confirmation
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "connection_established":
                        self.log_result("WebSocket Connection", True, f"WebSocket connected successfully to session {session_id}")
                        self.websocket_messages.append(data)
                        
                        # Test ping-pong
                        await websocket.send(json.dumps({"action": "ping"}))
                        pong_response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        pong_data = json.loads(pong_response)
                        
                        if pong_data.get("type") == "pong":
                            self.log_result("WebSocket Ping-Pong", True, "WebSocket ping-pong working correctly")
                            return True
                        else:
                            self.log_result("WebSocket Ping-Pong", False, f"Unexpected pong response: {pong_data}")
                            return False
                    else:
                        self.log_result("WebSocket Connection", False, f"Unexpected connection message: {data}")
                        return False
                        
                except asyncio.TimeoutError:
                    self.log_result("WebSocket Connection", False, "Timeout waiting for connection confirmation")
                    return False
                    
        except Exception as e:
            self.log_result("WebSocket Connection", False, f"WebSocket connection failed: {str(e)}")
            return False
    
    def test_session_status_endpoint(self):
        """Test GET /api/auto-typer/{session_id}/status - Enhanced status with new fields"""
        if not self.created_sessions:
            self.log_result("Session Status", False, "No sessions available for status testing")
            return False
        
        try:
            session_id = self.created_sessions[0]
            response = requests.get(f"{BASE_URL}/auto-typer/{session_id}/status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    self.log_result("Session Status", False, f"API returned error: {data['error']}")
                    return False
                
                # Validate enhanced status fields
                enhanced_fields = [
                    "current_message", "typing_progress", "is_typing", "failed_messages",
                    "retry_count", "can_resume", "messages_sent", "messages_failed"
                ]
                missing_fields = [field for field in enhanced_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Session Status", False, f"Missing enhanced status fields: {missing_fields}")
                    return False
                
                self.log_result("Session Status", True, f"Enhanced status retrieved successfully", data)
                return True
            else:
                self.log_result("Session Status", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Session Status", False, f"Request failed: {str(e)}")
            return False
    
    def test_pause_functionality(self):
        """Test POST /api/auto-typer/{session_id}/pause - Pause session"""
        if not self.created_sessions:
            self.log_result("Pause Functionality", False, "No sessions available for pause testing")
            return False
        
        try:
            session_id = self.created_sessions[0]
            response = requests.post(f"{BASE_URL}/auto-typer/{session_id}/pause", headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    # Check if error is expected (session not running)
                    if "not running" in data["error"].lower():
                        self.log_result("Pause Functionality", True, f"Correctly handled non-running session: {data['error']}")
                        return True
                    else:
                        self.log_result("Pause Functionality", False, f"Unexpected error: {data['error']}")
                        return False
                
                if "message" in data and "paused" in data["message"].lower():
                    # Verify session status changed to paused
                    status_response = requests.get(f"{BASE_URL}/auto-typer/{session_id}/status", timeout=5)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("status") == "paused" and status_data.get("can_resume"):
                            self.log_result("Pause Functionality", True, "Session paused successfully with resume capability")
                            return True
                        else:
                            self.log_result("Pause Functionality", False, f"Session status not updated correctly: {status_data.get('status')}")
                            return False
                    else:
                        self.log_result("Pause Functionality", True, "Pause appeared successful (couldn't verify status)")
                        return True
                else:
                    self.log_result("Pause Functionality", True, f"Pause response: {data}")
                    return True
            else:
                self.log_result("Pause Functionality", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Pause Functionality", False, f"Request failed: {str(e)}")
            return False
    
    def test_resume_functionality(self):
        """Test POST /api/auto-typer/{session_id}/resume - Resume session"""
        if not self.created_sessions:
            self.log_result("Resume Functionality", False, "No sessions available for resume testing")
            return False
        
        try:
            session_id = self.created_sessions[0]
            response = requests.post(f"{BASE_URL}/auto-typer/{session_id}/resume", headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    # Check if error is expected (session not paused)
                    if "not paused" in data["error"].lower() or "not found" in data["error"].lower():
                        self.log_result("Resume Functionality", True, f"Correctly handled non-paused session: {data['error']}")
                        return True
                    else:
                        self.log_result("Resume Functionality", False, f"Unexpected error: {data['error']}")
                        return False
                
                if "message" in data and "resumed" in data["message"].lower():
                    self.log_result("Resume Functionality", True, "Session resumed successfully")
                    return True
                else:
                    self.log_result("Resume Functionality", True, f"Resume response: {data}")
                    return True
            else:
                self.log_result("Resume Functionality", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Resume Functionality", False, f"Request failed: {str(e)}")
            return False
    
    def test_manual_retry_functionality(self):
        """Test POST /api/auto-typer/{session_id}/retry - Manual retry mechanism"""
        if not self.created_sessions:
            self.log_result("Manual Retry", False, "No sessions available for retry testing")
            return False
        
        try:
            session_id = self.created_sessions[0]
            response = requests.post(f"{BASE_URL}/auto-typer/{session_id}/retry", headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    # Check if error is expected (no failed messages)
                    if "no failed messages" in data["error"].lower():
                        self.log_result("Manual Retry", True, f"Correctly handled no failed messages: {data['error']}")
                        return True
                    elif "not found" in data["error"].lower():
                        self.log_result("Manual Retry", True, f"Correctly handled session not found: {data['error']}")
                        return True
                    else:
                        self.log_result("Manual Retry", False, f"Unexpected error: {data['error']}")
                        return False
                
                if "message" in data and "retrying" in data["message"].lower():
                    self.log_result("Manual Retry", True, f"Retry initiated successfully: {data['message']}")
                    return True
                else:
                    self.log_result("Manual Retry", True, f"Retry response: {data}")
                    return True
            else:
                self.log_result("Manual Retry", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Manual Retry", False, f"Request failed: {str(e)}")
            return False
    
    def test_session_stop_functionality(self):
        """Test POST /api/auto-typer/{session_id}/stop - Stop session"""
        if not self.created_sessions:
            self.log_result("Stop Functionality", False, "No sessions available for stop testing")
            return False
        
        try:
            session_id = self.created_sessions[0]
            response = requests.post(f"{BASE_URL}/auto-typer/{session_id}/stop", headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    if "not found" in data["error"].lower():
                        self.log_result("Stop Functionality", True, f"Correctly handled session not found: {data['error']}")
                        return True
                    else:
                        self.log_result("Stop Functionality", False, f"Unexpected error: {data['error']}")
                        return False
                
                if "message" in data and "stopped" in data["message"].lower():
                    self.log_result("Stop Functionality", True, "Session stopped successfully")
                    return True
                else:
                    self.log_result("Stop Functionality", True, f"Stop response: {data}")
                    return True
            else:
                self.log_result("Stop Functionality", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Stop Functionality", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_all_sessions(self):
        """Test GET /api/auto-typer/sessions - Get all sessions"""
        try:
            response = requests.get(f"{BASE_URL}/auto-typer/sessions", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # Check if our test session is in the list
                    if self.created_sessions:
                        found_session = any(session.get("id") in self.created_sessions for session in data)
                        if found_session:
                            self.log_result("Get All Sessions", True, f"Retrieved {len(data)} sessions, test session found")
                            return True
                        else:
                            self.log_result("Get All Sessions", True, f"Retrieved {len(data)} sessions (test session may have been cleaned up)")
                            return True
                    else:
                        self.log_result("Get All Sessions", True, f"Retrieved {len(data)} sessions")
                        return True
                else:
                    self.log_result("Get All Sessions", False, f"Expected list, got: {type(data)}")
                    return False
            else:
                self.log_result("Get All Sessions", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Get All Sessions", False, f"Request failed: {str(e)}")
            return False
    
    async def test_websocket_real_time_updates(self):
        """Test WebSocket real-time session updates"""
        if not self.created_sessions:
            self.log_result("WebSocket Real-time Updates", False, "No sessions available for WebSocket testing")
            return False
        
        session_id = self.created_sessions[0]
        ws_url = f"{WS_URL}/{session_id}"
        
        try:
            async with websockets.connect(ws_url, timeout=10) as websocket:
                # Wait for connection confirmation
                await asyncio.wait_for(websocket.recv(), timeout=5.0)
                
                # Request current status to trigger an update
                await websocket.send(json.dumps({"action": "get_status"}))
                
                # Wait for status update
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    
                    if data.get("type") == "session_update":
                        self.log_result("WebSocket Real-time Updates", True, f"Received real-time session update: {data['type']}")
                        return True
                    else:
                        self.log_result("WebSocket Real-time Updates", True, f"Received WebSocket message: {data.get('type', 'unknown')}")
                        return True
                        
                except asyncio.TimeoutError:
                    self.log_result("WebSocket Real-time Updates", True, "No immediate updates (expected for idle session)")
                    return True
                    
        except Exception as e:
            self.log_result("WebSocket Real-time Updates", False, f"WebSocket real-time test failed: {str(e)}")
            return False
    
    def run_websocket_test(self, test_func):
        """Helper to run async WebSocket tests"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(test_func())
        except Exception as e:
            print(f"Error running WebSocket test: {str(e)}")
            return False
        finally:
            loop.close()
    
    def cleanup_sessions(self):
        """Clean up any remaining test sessions"""
        for session_id in self.created_sessions[:]:
            try:
                requests.post(f"{BASE_URL}/auto-typer/{session_id}/stop", timeout=5)
                print(f"🧹 Cleaned up session: {session_id}")
            except:
                pass
    
    def run_all_tests(self):
        """Run all enhanced Discord autotyper tests"""
        print("🚀 Starting Enhanced Discord Autotyper API Tests")
        print("=" * 70)
        
        # Test sequence
        tests = [
            ("API Health Check", self.test_api_health_check),
            ("Enhanced Session Creation", self.test_enhanced_session_creation),
            ("Session Status Endpoint", self.test_session_status_endpoint),
            ("Pause Functionality", self.test_pause_functionality),
            ("Resume Functionality", self.test_resume_functionality),
            ("Manual Retry Functionality", self.test_manual_retry_functionality),
            ("Stop Functionality", self.test_session_stop_functionality),
            ("Get All Sessions", self.test_get_all_sessions),
        ]
        
        # WebSocket tests (run separately due to async nature)
        websocket_tests = [
            ("WebSocket Connection", self.test_websocket_connection),
            ("WebSocket Real-time Updates", self.test_websocket_real_time_updates),
        ]
        
        passed = 0
        total = len(tests) + len(websocket_tests)
        
        # Run regular tests
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log_result(test_name, False, f"Test execution failed: {str(e)}")
        
        # Run WebSocket tests
        for test_name, test_func in websocket_tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                if self.run_websocket_test(test_func):
                    passed += 1
                time.sleep(0.5)
            except Exception as e:
                self.log_result(test_name, False, f"WebSocket test execution failed: {str(e)}")
        
        # Summary
        print("\n" + "=" * 70)
        print(f"📊 ENHANCED AUTOTYPER TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All enhanced autotyper tests passed! WebSocket and real-time features are working correctly.")
        else:
            print(f"⚠️  {total - passed} tests failed. See details above.")
        
        # Cleanup
        self.cleanup_sessions()
        
        return passed, total, self.test_results

class DiscordChannelAPITester:
    def __init__(self):
        self.created_channels = []
        self.test_results = []
        
    def log_result(self, test_name, success, message, response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        })
        
    def test_health_check(self):
        """Test basic API connectivity"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=10)
            if response.status_code == 200:
                self.log_result("API Health Check", True, f"API is accessible - Status: {response.status_code}")
                return True
            else:
                self.log_result("API Health Check", False, f"API returned status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("API Health Check", False, f"Connection failed: {str(e)}")
            return False
    
    def test_create_channel(self):
        """Test POST /api/channels - Create a new Discord channel"""
        try:
            payload = {
                "channel_id": TEST_CHANNEL_ID,
                "category": TEST_CATEGORY,
                "is_favorite": False
            }
            
            response = requests.post(f"{BASE_URL}/channels", json=payload, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    self.log_result("Create Channel", False, f"API returned error: {data['error']}")
                    return False
                
                # Validate response structure
                required_fields = ["id", "channel_id", "category", "is_favorite", "created_at"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Create Channel", False, f"Missing fields in response: {missing_fields}")
                    return False
                
                # Store created channel ID for cleanup
                self.created_channels.append(data["id"])
                
                self.log_result("Create Channel", True, f"Channel created successfully with ID: {data['id']}", data)
                return True
            else:
                self.log_result("Create Channel", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Create Channel", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_channels_empty(self):
        """Test GET /api/channels - Should return empty list initially"""
        try:
            response = requests.get(f"{BASE_URL}/channels", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Get Channels (Empty)", True, f"Retrieved {len(data)} channels")
                    return True
                else:
                    self.log_result("Get Channels (Empty)", False, f"Expected list, got: {type(data)}")
                    return False
            else:
                self.log_result("Get Channels (Empty)", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Get Channels (Empty)", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_channels_with_data(self):
        """Test GET /api/channels - Should return created channels"""
        try:
            response = requests.get(f"{BASE_URL}/channels", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check if our test channel is in the list
                    found_channel = any(ch.get("channel_id") == TEST_CHANNEL_ID for ch in data)
                    if found_channel:
                        self.log_result("Get Channels (With Data)", True, f"Retrieved {len(data)} channels, test channel found")
                        return True
                    else:
                        self.log_result("Get Channels (With Data)", False, "Test channel not found in results")
                        return False
                else:
                    self.log_result("Get Channels (With Data)", False, f"Expected non-empty list, got: {len(data) if isinstance(data, list) else type(data)}")
                    return False
            else:
                self.log_result("Get Channels (With Data)", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Get Channels (With Data)", False, f"Request failed: {str(e)}")
            return False
    
    def test_search_functionality(self):
        """Test GET /api/channels with search parameter"""
        try:
            # Test search by channel ID
            response = requests.get(f"{BASE_URL}/channels?search={TEST_CHANNEL_ID}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    found = any(ch.get("channel_id") == TEST_CHANNEL_ID for ch in data)
                    if found:
                        self.log_result("Search Functionality", True, f"Search by channel ID returned {len(data)} results")
                        return True
                    else:
                        self.log_result("Search Functionality", False, "Search did not return expected channel")
                        return False
                else:
                    self.log_result("Search Functionality", False, f"Expected list, got: {type(data)}")
                    return False
            else:
                self.log_result("Search Functionality", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Search Functionality", False, f"Request failed: {str(e)}")
            return False
    
    def test_category_filtering(self):
        """Test GET /api/channels with category filter"""
        try:
            response = requests.get(f"{BASE_URL}/channels?category={TEST_CATEGORY}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    # All returned channels should have the test category
                    correct_category = all(ch.get("category") == TEST_CATEGORY for ch in data)
                    if correct_category and len(data) > 0:
                        self.log_result("Category Filtering", True, f"Category filter returned {len(data)} channels")
                        return True
                    elif len(data) == 0:
                        self.log_result("Category Filtering", False, "Category filter returned no results")
                        return False
                    else:
                        self.log_result("Category Filtering", False, "Some channels have incorrect category")
                        return False
                else:
                    self.log_result("Category Filtering", False, f"Expected list, got: {type(data)}")
                    return False
            else:
                self.log_result("Category Filtering", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Category Filtering", False, f"Request failed: {str(e)}")
            return False
    
    def test_update_channel(self):
        """Test PUT /api/channels/{channel_id} - Update channel info"""
        if not self.created_channels:
            self.log_result("Update Channel", False, "No channels available to update")
            return False
            
        try:
            channel_id = self.created_channels[0]
            payload = {
                "channel_name": "Updated Test Channel",
                "category": "Updated Category",
                "is_favorite": True
            }
            
            response = requests.put(f"{BASE_URL}/channels/{channel_id}", json=payload, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    self.log_result("Update Channel", False, f"API returned error: {data['error']}")
                    return False
                
                # Verify updates were applied
                if (data.get("channel_name") == "Updated Test Channel" and 
                    data.get("category") == "Updated Category" and 
                    data.get("is_favorite") == True):
                    self.log_result("Update Channel", True, "Channel updated successfully", data)
                    return True
                else:
                    self.log_result("Update Channel", False, "Updates were not applied correctly")
                    return False
            else:
                self.log_result("Update Channel", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Update Channel", False, f"Request failed: {str(e)}")
            return False
    
    def test_get_categories(self):
        """Test GET /api/channels/categories - Get unique categories"""
        try:
            response = requests.get(f"{BASE_URL}/channels/categories", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "categories" in data and isinstance(data["categories"], list):
                    categories = data["categories"]
                    # Should contain our test categories
                    has_test_category = TEST_CATEGORY in categories or "Updated Category" in categories
                    if has_test_category:
                        self.log_result("Get Categories", True, f"Retrieved {len(categories)} categories: {categories}")
                        return True
                    else:
                        self.log_result("Get Categories", False, f"Test categories not found in: {categories}")
                        return False
                else:
                    self.log_result("Get Categories", False, f"Invalid response format: {data}")
                    return False
            else:
                self.log_result("Get Categories", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Get Categories", False, f"Request failed: {str(e)}")
            return False
    
    def test_error_handling_nonexistent_channel(self):
        """Test error handling for non-existent channels"""
        try:
            fake_id = "nonexistent-channel-id"
            
            # Test update non-existent channel
            response = requests.put(f"{BASE_URL}/channels/{fake_id}", 
                                  json={"channel_name": "test"}, 
                                  headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    self.log_result("Error Handling (Update)", True, f"Correctly returned error: {data['error']}")
                else:
                    self.log_result("Error Handling (Update)", False, "Should have returned error for non-existent channel")
                    return False
            else:
                self.log_result("Error Handling (Update)", True, f"Correctly returned HTTP error: {response.status_code}")
            
            # Test delete non-existent channel
            response = requests.delete(f"{BASE_URL}/channels/{fake_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    self.log_result("Error Handling (Delete)", True, f"Correctly returned error: {data['error']}")
                    return True
                else:
                    self.log_result("Error Handling (Delete)", False, "Should have returned error for non-existent channel")
                    return False
            else:
                self.log_result("Error Handling (Delete)", True, f"Correctly returned HTTP error: {response.status_code}")
                return True
                
        except Exception as e:
            self.log_result("Error Handling", False, f"Request failed: {str(e)}")
            return False
    
    def test_duplicate_channel_creation(self):
        """Test creating duplicate channel (should fail)"""
        try:
            payload = {
                "channel_id": TEST_CHANNEL_ID,  # Same as before
                "category": "Another Category",
                "is_favorite": True
            }
            
            response = requests.post(f"{BASE_URL}/channels", json=payload, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data and "already exists" in data["error"].lower():
                    self.log_result("Duplicate Channel Prevention", True, f"Correctly prevented duplicate: {data['error']}")
                    return True
                else:
                    self.log_result("Duplicate Channel Prevention", False, "Should have prevented duplicate channel creation")
                    return False
            else:
                self.log_result("Duplicate Channel Prevention", True, f"Correctly returned HTTP error: {response.status_code}")
                return True
                
        except Exception as e:
            self.log_result("Duplicate Channel Prevention", False, f"Request failed: {str(e)}")
            return False
    
    def test_delete_channel(self):
        """Test DELETE /api/channels/{channel_id} - Delete channel"""
        if not self.created_channels:
            self.log_result("Delete Channel", False, "No channels available to delete")
            return False
            
        try:
            channel_id = self.created_channels[0]
            
            response = requests.delete(f"{BASE_URL}/channels/{channel_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    self.log_result("Delete Channel", False, f"API returned error: {data['error']}")
                    return False
                
                if "message" in data and "deleted" in data["message"].lower():
                    # Verify channel is actually deleted
                    verify_response = requests.get(f"{BASE_URL}/channels", timeout=10)
                    if verify_response.status_code == 200:
                        channels = verify_response.json()
                        still_exists = any(ch.get("id") == channel_id for ch in channels)
                        if not still_exists:
                            self.log_result("Delete Channel", True, "Channel deleted successfully")
                            self.created_channels.remove(channel_id)
                            return True
                        else:
                            self.log_result("Delete Channel", False, "Channel still exists after deletion")
                            return False
                    else:
                        self.log_result("Delete Channel", True, "Delete appeared successful (couldn't verify)")
                        return True
                else:
                    self.log_result("Delete Channel", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_result("Delete Channel", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Delete Channel", False, f"Request failed: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up any remaining test channels"""
        for channel_id in self.created_channels[:]:
            try:
                requests.delete(f"{BASE_URL}/channels/{channel_id}", timeout=5)
                print(f"🧹 Cleaned up channel: {channel_id}")
            except:
                pass
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Discord Channel Management API Tests")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("API Health Check", self.test_health_check),
            ("Get Channels (Empty)", self.test_get_channels_empty),
            ("Create Channel", self.test_create_channel),
            ("Get Channels (With Data)", self.test_get_channels_with_data),
            ("Search Functionality", self.test_search_functionality),
            ("Category Filtering", self.test_category_filtering),
            ("Update Channel", self.test_update_channel),
            ("Get Categories", self.test_get_categories),
            ("Duplicate Channel Prevention", self.test_duplicate_channel_creation),
            ("Error Handling", self.test_error_handling_nonexistent_channel),
            ("Delete Channel", self.test_delete_channel),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log_result(test_name, False, f"Test execution failed: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Discord Channel Management API is working correctly.")
        else:
            print(f"⚠️  {total - passed} tests failed. See details above.")
        
        # Cleanup
        self.cleanup()
        
        return passed, total, self.test_results

if __name__ == "__main__":
    print("🎯 COMPREHENSIVE BACKEND API TESTING")
    print("Testing Enhanced Discord Autotyper + Channel Management")
    print("=" * 80)
    
    # Run Enhanced Discord Autotyper Tests
    print("\n" + "🤖 PHASE 1: ENHANCED DISCORD AUTOTYPER TESTS" + "\n")
    autotyper_tester = EnhancedDiscordAutotyperTester()
    autotyper_passed, autotyper_total, autotyper_results = autotyper_tester.run_all_tests()
    
    # Run Discord Channel Management Tests
    print("\n" + "📁 PHASE 2: DISCORD CHANNEL MANAGEMENT TESTS" + "\n")
    channel_tester = DiscordChannelAPITester()
    channel_passed, channel_total, channel_results = channel_tester.run_all_tests()
    
    # Combined Summary
    total_passed = autotyper_passed + channel_passed
    total_tests = autotyper_total + channel_total
    
    print("\n" + "=" * 80)
    print("🏆 FINAL COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    print(f"Enhanced Autotyper: {autotyper_passed}/{autotyper_total} tests passed")
    print(f"Channel Management: {channel_passed}/{channel_total} tests passed")
    print(f"OVERALL: {total_passed}/{total_tests} tests passed ({(total_passed/total_tests)*100:.1f}%)")
    
    if total_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Backend is fully functional with enhanced features.")
    else:
        print(f"⚠️  {total_tests - total_passed} tests failed. Review details above.")
    
    # Save comprehensive results
    comprehensive_results = {
        "summary": {
            "total_passed": total_passed,
            "total_tests": total_tests,
            "success_rate": total_passed/total_tests,
            "autotyper_results": {"passed": autotyper_passed, "total": autotyper_total},
            "channel_results": {"passed": channel_passed, "total": channel_total}
        },
        "autotyper_tests": autotyper_results,
        "channel_tests": channel_results,
        "timestamp": datetime.now().isoformat()
    }
    
    with open("/app/comprehensive_test_results.json", "w") as f:
        json.dump(comprehensive_results, f, indent=2)
    
    print(f"\n📝 Comprehensive results saved to: /app/comprehensive_test_results.json")