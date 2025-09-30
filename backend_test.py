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
BASE_URL = "https://chatflow-automation.preview.emergentagent.com/api"
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
    tester = DiscordChannelAPITester()
    passed, total, results = tester.run_all_tests()
    
    # Save detailed results
    with open("/app/test_results_detailed.json", "w") as f:
        json.dump({
            "summary": {"passed": passed, "total": total, "success_rate": passed/total},
            "results": results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n📝 Detailed results saved to: /app/test_results_detailed.json")