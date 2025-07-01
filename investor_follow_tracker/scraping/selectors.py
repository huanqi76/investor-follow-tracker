#ember1644 > span
#ember1673 > span
#ember1705 > span
#ember1737 > span

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# --- CONFIG -------------------------------------------------
START_URL = "https://example.com/articles"
CONTENT_SEL = ".card-title"        # CSS of the text elements
NEXT_BTN_SEL = "a[rel='next']"     # CSS of the "next page" button
SCROLL_PAUSE = 1.0                 # seconds to wait after each scroll
MAX_IDLE_SCROLLS = 3               # stop scrolling after this many no-growth cycles
# ------------------------------------------------------------

driver = webdriver.Chrome()
driver.get(START_URL)

texts = []
seen = set()

def scroll_and_collect():
    """Scroll to bottom, grabbing new elements as they appear."""
    idle_rounds = 0
    last_height = driver.execute_script("return document.body.scrollHeight")

    while idle_rounds < MAX_IDLE_SCROLLS:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)

        # collect items currently in DOM
        for el in driver.find_elements(By.CSS_SELECTOR, CONTENT_SEL):
            txt = el.text.strip()
            if txt and txt not in seen:
                texts.append(txt)
                seen.add(txt)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            idle_rounds += 1
        else:
            idle_rounds = 0
            last_height = new_height

def click_next_if_exists():
    """Return True if we clicked a new page, False if no more pages."""
    try:
        next_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, NEXT_BTN_SEL))
        )
        driver.execute_script("arguments[0].click();", next_btn)
        WebDriverWait(driver, 10).until(
            EC.staleness_of(next_btn)
        )  # wait for navigation
        return True
    except Exception:
        return False

# ---------- MAIN LOOP -----------------
page = 1
while True:
    print(f"Scraping page {page}")
    scroll_and_collect()
    if not click_next_if_exists():
        break
    page += 1
# --------------------------------------

driver.quit()

# do whatever you need with `texts`
print(f"Collected {len(texts)} unique rows")
