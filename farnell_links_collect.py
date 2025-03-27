import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random
import time
import pandas as pd
import logging
import re
import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


# Define custom formatter for colored logs
class CustomFormatter(logging.Formatter):
    BLUE = "\033[1;34m"  # For timestamp
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


# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler setup
console_handler = logging.StreamHandler()
console_handler.setFormatter(CustomFormatter())
logger.addHandler(console_handler)


# Driver setup
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


def human_like_scroll_to_pagination(driver):
    pagination_found = False
    max_scroll_attempts = 15
    attempt = 0
    while not pagination_found and attempt < max_scroll_attempts:
        try:
            pagination_button = driver.find_element(
                By.CSS_SELECTOR, ".bx--pagination__button--forward"
            )
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                pagination_button,
            )
            if pagination_button.is_displayed():
                pagination_found = True
                logger.info("Pagination button found and visible.")
            else:
                raise NoSuchElementException("Pagination button is not visible.")
        except NoSuchElementException:
            scroll_distance = random.randint(500, 1000)
            driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
            time.sleep(random.uniform(1, 3))
            attempt += 1
    if not pagination_found:
        logger.warning("Pagination button not found after maximum attempts.")
    return pagination_found


def click_show_results_if_present(driver):
    try:
        show_results_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    '[data-testid="catalog.productFilters.show-results-container__show-results-button"]',
                )
            )
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            show_results_button,
        )
        show_results_button.click()
        logger.info("Clicked 'Pokaż wyniki' button.")
        time.sleep(random.uniform(2, 4))
    except (TimeoutException, NoSuchElementException):
        logger.info("No 'Pokaż wyniki' button found, proceeding without clicking.")


def scrape_page_data(driver, processed_ids):
    data = []
    try:
        click_show_results_if_present(driver)

        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located(
                (
                    By.CSS_SELECTOR,
                    "tbody.ProductListerTablestyles__TableBody-sc-j76asa-8 tr.ProductListerTablestyles__TableRow-sc-j76asa-5",
                )
            )
        )
        rows = driver.find_elements(
            By.CSS_SELECTOR,
            "tbody.ProductListerTablestyles__TableBody-sc-j76asa-8 tr.ProductListerTablestyles__TableRow-sc-j76asa-5",
        )
        logger.info(f"Found {len(rows)} product rows on this page.")

        for idx, row in enumerate(rows, 1):
            product_data = {}
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'start'});",
                row,
            )
            time.sleep(random.uniform(0.5, 1.5))

            try:
                order_code_elem = row.find_element(
                    By.CLASS_NAME, "OrderCodeTableCellstyles__OrderValue-sc-1oup0u7-1"
                )
                farnell_part_number = (
                    order_code_elem.text.strip() if order_code_elem else "N/A"
                )
                product_data["Farnell Part Number"] = farnell_part_number

                if farnell_part_number in processed_ids:
                    logger.warning(
                        f"Duplicate product found: Farnell Part Number {farnell_part_number}, skipping."
                    )
                    continue
                processed_ids.add(farnell_part_number)
            except NoSuchElementException:
                product_data["Farnell Part Number"] = "N/A"
                logger.warning(
                    f"Row {idx}: Farnell part number not found, skipping row."
                )
                continue

            try:
                manuf_part_elem = row.find_element(
                    By.CLASS_NAME,
                    "ManufacturerPartNoTableCellstyles__PartNumber-sc-9z3ajz-3",
                )
                product_data["Manufacturer Part Number"] = (
                    manuf_part_elem.text.strip() if manuf_part_elem else "N/A"
                )
            except NoSuchElementException:
                product_data["Manufacturer Part Number"] = "N/A"
                logger.warning(f"Row {idx}: Manufacturer part number not found.")

            try:
                datasheet_link_elem = row.find_element(
                    By.CSS_SELECTOR,
                    ".DataSheetAttachmentstyles__DataSheetAttachment-sc-3ekebv-0 a",
                )
                product_data["Datasheet Link"] = (
                    datasheet_link_elem.get_attribute("href")
                    if datasheet_link_elem
                    else "N/A"
                )
            except NoSuchElementException:
                product_data["Datasheet Link"] = "N/A"
                logger.warning(f"Row {idx}: Datasheet link not found.")

            try:
                availability_elem = row.find_element(
                    By.CLASS_NAME,
                    "AvailabilityPrimaryStatusstyles__StatusMessage-sc-101ypue-2",
                )
                availability_text = (
                    availability_elem.text.strip() if availability_elem else "N/A"
                )
                stock_match = re.search(r"(\d+)", availability_text)
                product_data["Stock Quantity"] = (
                    stock_match.group(1) if stock_match else "N/A"
                )
            except NoSuchElementException:
                product_data["Stock Quantity"] = "N/A"
                logger.warning(f"Row {idx}: Stock quantity not found.")

            try:
                price_breakup_elem = row.find_element(
                    By.CSS_SELECTOR,
                    '[data-testid="catalog.listerTable.table-cell__price-breakup"]',
                )
                price_elements = price_breakup_elem.find_elements(
                    By.CLASS_NAME, "PriceBreakupTableCellstyles__Price-sc-ylr3xn-6"
                )
                qty_elements = price_breakup_elem.find_elements(
                    By.CLASS_NAME,
                    "PriceBreakupTableCellstyles__BaseQuantity-sc-ylr3xn-3",
                )
                for qty_elem, price_elem in zip(qty_elements, price_elements):
                    qty_text = qty_elem.text.strip().replace("+", "")
                    price_text = (
                        price_elem.text.strip()
                        .replace("zł", "")
                        .replace(" ", "")
                        .replace(",", ".")
                    )
                    product_data[f"Price {qty_text}"] = price_text
            except NoSuchElementException:
                logger.warning(f"Row {idx}: Price breakup not found.")

            data.append(product_data)
    except Exception as e:
        logger.error(f"Error while scraping page data: {str(e)}")
    return data


def main():
    url = "https://pl.farnell.com/en-PL/c/sensors-transducers/sensors/voltage-sensors-transducers?ICID=I-SF-LEM-VOLTAGE_TRANSDUCERS-JUNE23-WF3287013&brand=lem"
    output_file = "farnell_data.xlsx"
    proxy = None

    driver = setup_driver(proxy)
    all_data = []
    processed_ids = set()

    try:
        logger.info("=== Starting Scraping Process ===")
        logger.info(f"Navigating to: {url}")
        driver.get(url)
        time.sleep(random.uniform(3, 5))

        page_number = 1
        while True:
            logger.info(f"Processing page {page_number}...")
            if not human_like_scroll_to_pagination(driver):
                logger.info("Pagination button not found, finishing scraping.")
                break

            page_data = scrape_page_data(driver, processed_ids)
            all_data.extend(page_data)
            logger.info(
                f"Collected {len(page_data)} unique products from page {page_number}. Total unique products: {len(all_data)}."
            )

            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            ".bx--pagination__button--forward:not(.bx--btn--disabled)",
                        )
                    )
                )
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                    next_button,
                )
                next_button.click()
                time.sleep(random.uniform(3, 6))
                page_number += 1
            except (NoSuchElementException, TimeoutException):
                logger.info("Next button not found or disabled, finishing scraping.")
                break

        if all_data:
            df = pd.DataFrame(all_data)
            df.to_excel(output_file, index=False, engine="openpyxl")
            logger.info(
                f"Scraping completed! Data saved to {output_file}. Total unique products: {len(all_data)}."
            )
        else:
            logger.warning("No data collected to save.")
        logger.info("=== Scraping Process Finished ===")

    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Browser closed.")
            except Exception as e:
                logger.error(f"Error while closing browser: {e}")
            finally:
                time.sleep(2)


if __name__ == "__main__":
    main()
