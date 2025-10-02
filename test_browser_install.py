#!/usr/bin/env python3
"""Test script to verify Playwright browser installation"""
import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_browser():
    """Test if Playwright can launch browser"""
    try:
        logger.info("Testing Playwright browser installation...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Test navigation
            await page.goto('https://httpbin.org/get', wait_until='networkidle')
            title = await page.title()
            
            logger.info(f"Successfully navigated to page with title: {title}")
            
            await browser.close()
            logger.info("✅ Browser test completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Browser test failed: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_browser())
    if result:
        print("✅ Playwright browser installation is working correctly")
    else:
        print("❌ Playwright browser installation has issues")