import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)
import random
import time
import json
import os
import logging

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


# Define custom formatter
class CustomFormatter(logging.Formatter):
    BLUE = "\033[1;34m"  # For DATE
    GREEN = "\033[1;32m"  # For INFO
    YELLOW = "\033[1;33m"  # For WARNING
    RED = "\033[1;31m"  # For ERROR
    RESET = "\033[0m"  # Clear formatting

    FORMATS = {
        logging.INFO: f"{BLUE}%(asctime)s - %(levelname)s:{RESET} {GREEN}%(message)s{RESET}",
        logging.WARNING: f"{BLUE}%(asctime)s - %(levelname)s:{RESET} {YELLOW}%(message)s{RESET}",
        logging.ERROR: f"{BLUE}%(asctime)s - %(levelname)s:{RESET} {RED}%(message)s{RESET}",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self._style._fmt)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


# Logger settings
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(CustomFormatter())
logger.addHandler(console_handler)

COOKIES_FILE = "cookies.json"


# Functions for working with cookies
def save_cookies(driver):
    cookies = driver.get_cookies()
    with open(COOKIES_FILE, "w") as f:
        json.dump(cookies, f)
    logger.info("Cookies successfully created.")


def load_cookies(driver):
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        logger.info("Cookies successfully loaded.")


# Functions for human-like behavior
def human_like_scroll_to_pagination(driver):
    pagination_found = False
    while not pagination_found:
        try:
            pagination = driver.find_element(By.ID, "bottom-plp-pagination")
            if pagination.is_displayed():
                pagination_found = True
                logger.info("Pagination element not found.")
            else:
                raise NoSuchElementException("Pagination not visible.")
        except NoSuchElementException:
            scroll_distance = random.randint(100, 300)
            driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
            time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            logger.error(f"Error while scrolling: {e}")
            break
    return pagination_found


def human_like_mouse_move(driver):
    actions = ActionChains(driver)
    for _ in range(random.randint(3, 7)):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, "a, button, div")
            visible_elements = [
                elem for elem in elements if elem.is_displayed() and elem.is_enabled()
            ]
            if not visible_elements:
                logger.warning("There are no visible elements to move the cursor to.")
                return
            elem = random.choice(visible_elements)
            actions.move_to_element(elem).perform()
            time.sleep(random.uniform(0.2, 0.7))
        except StaleElementReferenceException:
            logger.warning("One of the elements has become stale, skipping.")
            continue
        except Exception as e:
            logger.error(f"Error while moving the cursor: {e}")
            continue
    logger.info("Cursor movement successfully completed.")


def collect_links(driver, collected_links):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "a.name.product-name-and-price")
            )
        )
        link_elements = driver.find_elements(
            By.CSS_SELECTOR, "a.name.product-name-and-price"
        )
        for elem in link_elements:
            href = elem.get_attribute("href")
            if href and href not in collected_links:
                collected_links.add(href)
                logger.info(f"New link: {href}")
        logger.info(f"Collected links: {len(collected_links)}")
    except Exception as e:
        logger.error(f"Error while collecting links: {e}")


def setup_driver(proxy=None):
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    chrome_options.add_argument("--accept-language=en-US,en;q=0.9")
    if proxy:
        chrome_options.add_argument(f"--proxy-server={proxy}")
        logger.info(f"Using proxy: {proxy}")
    driver = uc.Chrome(
        options=chrome_options,
        executable_path=os.getenv("executable_path"),
        headless=False,
    )
    return driver


def main():
    url = "https://www.elfadistrelec.pl/pl/manufacturer/lem/man_lem/"
    output_file = "elfadistrelec_collected_links.txt"
    collected_links = set()
    proxy = None

    max_pages = input("Input the maximum number of pages to parse:")
    max_pages = int(max_pages)

    driver = setup_driver(proxy)
    try:
        logger.info("Starting the parsing process.")
        logger.info(f"Opening the URL: {url}")
        driver.get(url)
        time.sleep(random.uniform(3, 5))
        load_cookies(driver)
        driver.refresh()
        time.sleep(random.uniform(2, 4))

        page_number = 1
        while page_number <= max_pages:
            logger.info(f"Parsing page {page_number}...")
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a, button, div"))
            )
            human_like_mouse_move(driver)
            pagination_found = human_like_scroll_to_pagination(driver)
            if not pagination_found:
                logger.warning("Pagination not found, exiting.")
                break
            collect_links(driver, collected_links)

            if page_number == max_pages:
                logger.info("Maximum number of pages reached, exiting.")
                break

            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "bottom-pagination-next-button"))
                )
                actions = ActionChains(driver)
                actions.move_to_element(next_button).pause(
                    random.uniform(0.5, 1.5)
                ).click().perform()
                time.sleep(random.uniform(3, 6))
                page_number += 1
            except (NoSuchElementException, ElementNotInteractableException):
                logger.info("Button 'NEXT' not found or not clickable, exiting.")
                break
            except Exception as e:
                logger.error(f"Error while clicking the 'NEXT' button: {e}")
                break

        save_cookies(driver)
        with open(output_file, "w", encoding="utf-8") as f:
            for link in collected_links:
                f.write(link + "\n")
        logger.info(
            f"Collecting completed. Collected links: {len(collected_links)}. Results saved to {output_file}"
        )

    finally:
        if driver:
            time.sleep(2)
            driver.close()
            time.sleep(1)
            driver.quit()
            logger.info("Browser closed.")
        logger.info("Parsing completed.")


if __name__ == "__main__":
    main()
