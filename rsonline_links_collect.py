import asyncio
from pyppeteer import launch
import random
import json
import os
import logging

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


# Custom formatter for logging
class CustomFormatter(logging.Formatter):
    BLUE = "\033[1;34m"  # For the timestamp
    GREEN = "\033[1;32m"  # For INFO
    YELLOW = "\033[1;33m"  # For WARNING
    RED = "\033[1;31m"  # For ERROR
    RESET = "\033[0m"  # Color reset

    FORMATS = {
        logging.INFO: f"{BLUE}%(asctime)s - %(levelname)s:{RESET} {GREEN}%(message)s{RESET}",
        logging.WARNING: f"{BLUE}%(asctime)s - %(levelname)s:{RESET} {YELLOW}%(message)s{RESET}",
        logging.ERROR: f"{BLUE}%(asctime)s - %(levelname)s:{RESET} {RED}%(message)s{RESET}",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self._style._fmt)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


# Logger configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(CustomFormatter())
logger.addHandler(console_handler)


async def auto_scroll(page):
    await page.evaluate(
        """
        async () => {
            await new Promise(resolve => {
                let totalHeight = 0;
                let distance = 100;
                let timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    if(totalHeight >= document.body.scrollHeight) {
                        clearInterval(timer);
                        resolve();
                    }
                }, 200);
            });
        }
    """
    )


async def human_like_mouse_move(page):
    mouse = page.mouse
    for _ in range(random.randint(5, 15)):
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        await mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.1, 0.5))


async def main():
    logger.info("=== Starting Scraping Process ===")
    browser = await launch(
        headless=False,
        executablePath=os.getenv("executable_path"),
        args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--disable-gpu",
            "--disable-features=IsolateOrigins,site-per-process",
            "--start-maximized",
        ],
        userDataDir=os.path.abspath("./user_data"),
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False,
    )
    page = await browser.newPage()

    # Anti-bot detection:
    await page.evaluateOnNewDocument(
        """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    """
    )

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    await page.setUserAgent(user_agent)
    await page.setViewport({"width": 1920, "height": 1080})
    await page.setExtraHTTPHeaders(
        {"Accept-Language": "en-US,en;q=0.9", "Referer": "https://www.google.com/"}
    )

    cookies_file = "cookies.json"
    if os.path.exists(cookies_file):
        with open(cookies_file, "r") as f:
            cookies = json.load(f)
            await page.setCookie(*cookies)

    url = "https://pl.rs-online.com/web/c/automatyka-i-sterowanie/sterowanie-procesami/transformatory-pradu/?applied-dimensions=4294966292&pn=1"
    logger.info(f"Navigating to: {url}")
    await asyncio.sleep(random.uniform(2, 5))
    await page.goto(url, {"waitUntil": "domcontentloaded"})

    cookies = await page.cookies()
    with open(cookies_file, "w") as f:
        json.dump(cookies, f)

    collected_links = set()

    async def collect_links():
        links = await page.evaluate(
            """
            () => Array.from(document.querySelectorAll('a[data-qa="product-tile-container"]'))
                      .map(a => a.href)
        """
        )
        collected_links.update(links)

    async def click_next_page():
        try:
            await auto_scroll(page)
            next_button = await page.querySelector(
                '[data-testid="footer-pagination"] [data-testid="pagination-ion"] a[aria-label="Kolejna"]'
            )
            if next_button:
                await next_button.hover()
                await asyncio.sleep(random.uniform(0.5, 1.5))
                await next_button.click()
                await asyncio.sleep(random.uniform(2, 5))
                return True
            else:
                logger.warning("Button 'Kolejna' was not found or disabled.")
                return False
        except Exception as e:
            logger.error(f"Error while clicking the next page: {e}")
            return False

    page_number = 1
    while True:
        logger.info(f"Processing page {page_number}...")
        await human_like_mouse_move(page)
        await collect_links()
        await asyncio.sleep(random.uniform(2, 4))
        if not await click_next_page():
            break
        page_number += 1

    await browser.close()
    logger.info("=== Scraping Process Finished ===")

    with open("rsonline_collected_links.txt", "w", encoding="utf-8") as file:
        for link in collected_links:
            file.write(link + "\n")

    logger.info(
        f"Links collected: {len(collected_links)}. Results saved to rsonline_collected_links.txt."
    )


asyncio.get_event_loop().run_until_complete(main())
