# record_login.py
import asyncio, os, sys
from playwright.async_api import async_playwright, Error as PWError

LOGIN_URL   = "https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin"
USER_ENV    = "LINKEDIN_USERNAME"
PASS_ENV    = "LINKEDIN_PASSWORD"
STATE_FILE  = "state.json"        # where we cache the session

async def main() -> None:
    user = os.getenv(USER_ENV)
    pwd  = os.getenv(PASS_ENV)
    if not user or not pwd:
        sys.exit(f"✖ Set {USER_ENV} and {PASS_ENV} env vars first")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=250)
        context = await browser.new_context()          # fresh, empty profile
        page    = await context.new_page()

        await page.goto(LOGIN_URL)
        await page.wait_for_selector("#username")
        
        # await page.fill("input[name='username']", user)
        # await page.fill("input[name='password']", pwd)
        await page.fill("#username", user)
        await page.fill("#password", pwd)

        await page.click("button[type='submit']")      # adjust selector if needed
        # await page.wait_for_load_state("networkidle")  # logged-in homepage
        page.wait_for_url("**/dashboard")

        # ‼️ at this point you’re authenticated
        await context.storage_state(path=STATE_FILE)
        print(f"✓ saved session to {STATE_FILE}")
        await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except PWError as e:
        sys.exit(f"[Playwright error] {e}")
