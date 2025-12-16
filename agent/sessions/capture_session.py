"""
Utility to manually capture a browser session state after logging in.

Usage:
    python -m agent.sessions.capture_session --site blackboard --url https://utmb.blackboard.com
"""

import asyncio
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent


async def capture_session(site: str, url: str):
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: Run: pip install playwright && playwright install")
        return

    print(f"\n{'='*50}")
    print(f"  SESSION CAPTURE: {site}")
    print(f"{'='*50}")
    print(f"\nStarting URL: {url}")
    print("\nA browser will open. Log in manually.")
    print("When logged in successfully, CLOSE THE BROWSER.\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url)

        print("Waiting for you to log in and close the browser...")

        # Wait for browser to close
        while True:
            try:
                if len(context.pages) == 0:
                    break
                await asyncio.sleep(1)
            except:
                break

        # Save state
        output_path = ROOT / f"{site}_state.json"
        await context.storage_state(path=str(output_path))
        print(f"\nSession saved to: {output_path}")
        print("\nYou can now use this session in tasks with:")
        print(f'  session_state_path: "sessions/{site}_state.json"')

        await browser.close()


def main():
    parser = argparse.ArgumentParser(description="Capture browser session after manual login")
    parser.add_argument("--site", required=True, help="Site name (e.g., blackboard)")
    parser.add_argument("--url", required=True, help="Login page URL")
    args = parser.parse_args()

    asyncio.run(capture_session(args.site, args.url))


if __name__ == "__main__":
    main()
