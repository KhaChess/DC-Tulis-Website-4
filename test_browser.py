#!/usr/bin/env python3
"""
Simple test to check if Playwright browser automation works
"""

import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    try:
        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(headless=True)
            print("Browser launched successfully!")
            
            context = await browser.new_context()
            page = await context.new_page()
            
            print("Navigating to a test page...")
            await page.goto('https://httpbin.org/get')
            
            title = await page.title()
            print(f"Page title: {title}")
            
            await browser.close()
            print("Browser closed successfully!")
            return True
            
    except Exception as e:
        print(f"Browser test failed: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_browser())
    if result:
        print("✅ Browser automation is working!")
    else:
        print("❌ Browser automation failed!")