"""
Scrapes every record on a LinkedIn Interests tab that either
(a) auto-loads when you reach the bottom, or
(b) shows a “Show more results” button.

EDIT the ALL-CAP constants below if LinkedIn changes its DOM.
"""
import csv, pathlib, sys, textwrap
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from investor_follow_tracker.utils import *

# ─────────────────────────── USER SETTINGS ──────────────────────────────
START_URLS = build_linkedin_urls(fetch_handles())

SHOW_MORE_TEXT = "Show more results"

# one row per interest card
ITEM_SELECTOR = "*[id^='profilePagedListComponent'][id*='-COMPANIES-INTERESTS']"

# the company name inside the row
FULL_SELECTOR = (
    "*[id^='profilePagedListComponent'][id*='-COMPANIES-INTERESTS'] "
    "span:first-child"
)
# ─────────────────────────────────────────────────────────────────────────

# Safety knobs (tweak if LinkedIn is slow)
SCROLL_PAUSE_MS = 15000      # wait this long after each End / click
STALL_LIMIT     = 4         # end-presses with no new cards before give up
MAX_SCROLLS     = 300       # absolute cap (avoid infinite loop)

# ──────────────────────────── CORE LOGIC ────────────────────────────────
async def load_everything(ctx) -> None:
    """
    Scroll until ITEM_SELECTOR stops growing.
    • Always wheel-scroll the list container (never relies on End or buttons).
    • Waits only on the LinkedIn spinner — no networkidle, so no timeouts.
    """
    stalled, seen = 0, -1

    for _ in range(MAX_SCROLLS):
        # 1 ── scroll ~1 viewport on whichever element owns the scrollbar
        await ctx.evaluate("""
        () => {
            // 1) grab the first interest row
            const firstRow =
            document.querySelector('*[id^="profilePagedListComponent"]');
            if (!firstRow) return;

            // 2) walk up until we find an ancestor that can scroll
            const scrollBox = (function findScrollable(el) {
                while (el && el !== document.documentElement) {
                    const st = window.getComputedStyle(el);
                    if (
                        (st.overflowY === 'auto' || st.overflowY === 'scroll') &&
                        el.scrollHeight > el.clientHeight
                    ) return el;
                    el = el.parentElement;
                }
                return document.scrollingElement;          // fallback
            })(firstRow);

            // 3) move one viewport
            scrollBox.scrollBy({ top: scrollBox.clientHeight,
                                behavior: 'instant' });
        }
        """)

        # 2 ── wait for spinner cycle  (appears → disappears) or timeout
        try:
            # wait until spinner shows (max 5 s); ignore if it never appears
            await ctx.locator("div.artdeco-loader") \
                    .wait_for(state="attached", timeout=7_000)
            # then wait until it’s gone (max 15 s)
            await ctx.locator("div.artdeco-loader") \
                    .wait_for(state="detached", timeout=7_000)
        except PWTimeout:
            # Either spinner never appeared or stayed too long; keep going
            pass

        await ctx.wait_for_timeout(500)   # debounce

        # 3 ── progress check
        new_seen = await ctx.locator(ITEM_SELECTOR).count()
        if new_seen == seen:
            stalled += 1
            if stalled >= STALL_LIMIT:
                print("⇢ No new rows after", STALL_LIMIT, "tries — stopping.")
                break
        else:
            seen, stalled = new_seen, 0
            print(f"⇢ rows collected: {seen}")

async def scrape() -> None:
    async with async_playwright() as p:
        browser  = await p.chromium.launch(headless=False, slow_mo=250)
        context  = await browser.new_context(storage_state="investor_follow_tracker/auth/state.json")

        all_rows = []

        for url in START_URLS:

            page     = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=70000)   

            await page.wait_for_selector(
                "*[id^='profilePagedListComponent']",
                state="attached",
                timeout=15_000
            )
            print("Rows visible immediately:",
                await page.locator(ITEM_SELECTOR).count())

            candidate = await page.evaluate("""
            () => {
            const row = document.querySelector('*[id^="profilePagedListComponent"]');
            if (!row) return null;

            let el = row;
            while (el && el !== document.documentElement) {
                const style = window.getComputedStyle(el);
                const canScroll =
                (style.overflowY === 'auto' || style.overflowY === 'scroll') &&
                el.scrollHeight > el.clientHeight;

                if (canScroll) return el.className || el.id || '<<anonymous>>';
                el = el.parentElement;
            }
            return 'document';
            }
            """)
            print("⇢ Scroll container Playwright found →", candidate) 

            first_batch = await page.locator(ITEM_SELECTOR).count()
            if first_batch == 0:
                msg = textwrap.dedent(f"""
                    🛑 ITEM_SELECTOR matches 0 elements on the first screen.
                    Re-inspect the page and update ITEM_SELECTOR / FULL_SELECTOR.
                """)
                sys.exit(msg)

            await load_everything(page)
            names = await page.locator(FULL_SELECTOR).all_inner_texts()
            clean_names = [n.strip().split("\n")[0] for n in names]
            print(f"{url}  → scraped {len(clean_names)} names")

            run_rows = [[url, name, TODAY] for name in names]   #  ← add TODAY
            all_rows.extend(run_rows)

            await page.close()

        out = pathlib.Path(__file__).with_suffix(".csv")
        with out.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(all_rows)
        print(f"✓ wrote {len(all_rows)} rows → {out}")

        rows_for_sheet = clean_rows(all_rows)
        await push_to_gsheet(rows_for_sheet)# now dedups + highlights
        print(f"⇢ {len(all_rows)} rows processed this run")