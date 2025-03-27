import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
import random
import time
import pandas as pd
import logging
import re
import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


# Custom logging formatter
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
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(CustomFormatter())
logger.addHandler(console_handler)


# Function to load links from a file
def load_links(file_path="elfadistrelec_collected_links.txt"):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            links = [line.strip() for line in file.readlines() if line.strip()]
            logger.info(f"Loaded links: {len(links)}")
            return links
    except FileNotFoundError:
        logger.error(f"File {file_path} was not found.")
        return []


# Driver setup function
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
    logger.info("Driver successfully set up")
    return driver


# Function to scrape data from a product page
def scrape_data(driver, url):
    try:
        logger.info(f"Processing URL: {url}")
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pdp_product_title"))
        )
        time.sleep(random.uniform(1, 3))

        # 1. Product title
        title = "N/A"
        try:
            title_elem = driver.find_element(By.ID, "pdp_product_title")
            title = title_elem.text.strip() if title_elem else "N/A"
            logger.info(f"Product title: {title}")
        except NoSuchElementException:
            logger.warning(f"Product title not found for {url}")

        # 2. Stock quantity and delivery time
        stock_quantity = "N/A"
        delivery_time = "N/A"
        try:
            stock_elem = driver.find_element(By.ID, "pdp_stock_available_text")
            stock_text = stock_elem.text.strip() if stock_elem else "N/A"
            if stock_text != "N/A":
                stock_match = re.search(r"Ilość sztuk w magazynie:\s*(\d+)", stock_text)
                stock_quantity = stock_match.group(1) if stock_match else "N/A"
                parts = stock_text.split("Czas dostawy:")
                delivery_time = parts[1].strip() if len(parts) > 1 else "N/A"
            logger.info(
                f"Stock quantity: {stock_quantity}, Delivery time: {delivery_time}"
            )
        except NoSuchElementException:
            logger.warning(f"Stock quantity and delivery time not found for {url}")

        # 3. Prices
        price_exc_vat = "N/A"
        price_inc_vat = "N/A"
        try:
            price_holder = driver.find_element(By.ID, "pdp_product_price")
            price_exc_vat = (
                price_holder.find_element(By.ID, "pdp_product_price_currency_exc_vat")
                .text.strip()
                .replace("PLN", "")
                .strip()
                if price_holder.find_elements(
                    By.ID, "pdp_product_price_currency_exc_vat"
                )
                else "N/A"
            )
            price_inc_vat = (
                price_holder.find_element(By.ID, "pdp_product_price_currency_inc_vat")
                .text.strip()
                .replace("PLN", "")
                .strip()
                if price_holder.find_elements(
                    By.ID, "pdp_product_price_currency_inc_vat"
                )
                else "N/A"
            )
            logger.info(
                f"Price excl. VAT: {price_exc_vat}, Price incl. VAT: {price_inc_vat}"
            )
        except NoSuchElementException:
            logger.warning(f"Prices not found for {url}")

        # 4. Prices per quantity
        price_per_quantity = {}
        try:
            price_holder = driver.find_element(
                By.CLASS_NAME, "prices__priceholder-per-q"
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", price_holder)
            time.sleep(2)

            quantity_holder = price_holder.find_element(
                By.CLASS_NAME, "quantity-and-price-details"
            )
            quantities = quantity_holder.find_elements(By.CLASS_NAME, "quantity-item")
            logger.info(f"Quantity options found: {len(quantities)}")

            has_discounts = (
                "has-discounts" in price_holder.get_attribute("class").split()
            )
            if has_discounts:
                logger.info("Discounts found, waiting for prices to load.")
                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, ".prices__priceholder-per-q > .price-per-q")
                    )
                )
                actual_price_block = price_holder.find_element(
                    By.CSS_SELECTOR, ".price-per-q:not(.was-price)"
                )
                price_elements = actual_price_block.find_elements(
                    By.CSS_SELECTOR, 'div:not([id*="saving"])'
                )
                logger.info(f"Find prices in actual block: {len(price_elements)}")
            else:
                logger.info("Discounts not found, waiting for prices to load.")
                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located(
                        (
                            By.CSS_SELECTOR,
                            ".quantity-and-price-details .price-per-q > div",
                        )
                    )
                )
                price_elements = quantity_holder.find_elements(
                    By.CSS_SELECTOR, '.price-per-q > div:not([id*="saving"])'
                )
                logger.info(f"Prices found: {len(price_elements)}")

            for qty, price in zip(quantities, price_elements):
                qty_text = qty.text.strip().replace(" ", "")  # "1 +" -> "1+"
                price_text = price.text.strip().replace("PLN", "").strip()
                price_per_quantity[f"Price {qty_text}"] = price_text
                logger.info(f"Price for {qty_text}: {price_text}")
        except (NoSuchElementException, StaleElementReferenceException):
            logger.warning(f"Prices per quantity not found for {url}")
            price_per_quantity["Price 1+"] = price_exc_vat

        # 5. Document links
        document_links = []
        try:
            doc_section = driver.find_element(By.CLASS_NAME, "downloads-items")
            doc_elements = doc_section.find_elements(By.CLASS_NAME, "pdp-pdf-btn")
            for elem in doc_elements:
                doc_url = elem.get_attribute("href")
                document_links.append(doc_url)
            logger.info(f"Links to documents found: {len(document_links)}")
        except NoSuchElementException:
            logger.warning(f"Document links not found for {url}")
            document_links.append("N/A")

        # 6. Data from .copy-functions
        article_number = "N/A"
        part_number = "N/A"
        manufacturer = "N/A"
        try:
            copy_functions = driver.find_element(By.CLASS_NAME, "copy-functions")
            article_number_elem = copy_functions.find_element(By.ID, "js-productcode")
            article_number = (
                article_number_elem.text.strip() if article_number_elem else "N/A"
            )
            part_number_elem = copy_functions.find_element(
                By.ID, "pdp_manufacturer_number"
            )
            part_number = part_number_elem.text.strip() if part_number_elem else "N/A"
            manufacturer_elem = copy_functions.find_elements(
                By.CLASS_NAME, "copy-functions__info-number"
            )[-1]
            manufacturer = (
                manufacturer_elem.text.strip() if manufacturer_elem else "N/A"
            )
            logger.info(
                f"Article: {article_number}, Manufacturer number: {part_number}, Manufacturer: {manufacturer}"
            )
        except NoSuchElementException:
            logger.warning(f"Manufacturer data not found for {url}")

        # Constructing the final data dictionary
        data = {
            "Name": title,
            "Stock q-ty": stock_quantity,
            "Delivery time": delivery_time,
            "Price exc. VAT": price_exc_vat,
            "Price with VAT": price_inc_vat,
            "Art. number Elfa Distrelec": article_number,
            "Manufacturer number": part_number,
            "Manufacturer": manufacturer,
            "Documents": ", ".join(document_links) if document_links else "N/A",
        }
        data.update(price_per_quantity)

        return data

    except TimeoutException:
        logger.error(f"The page took too long to load: {url}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while processing {url}: {e}")
        return None


def main():
    logger.info("=== Starting the scraping process ===")
    links = load_links("elfadistrelec_collected_links.txt")

    driver = setup_driver()
    all_data = []

    try:
        for idx, link in enumerate(links, start=1):
            logger.info(f"({idx}/{len(links)}) Processing: {link}")
            data = scrape_data(driver, link)
            if data:
                all_data.append(data)
            time.sleep(random.uniform(2, 5))

        # Saving data to Excel
        df = pd.DataFrame(all_data)
        df.to_excel("elfadistrelec_data.xlsx", index=False, engine="openpyxl")
        logger.info("Data successfully saved to 'elfadistrelec_data.xlsx'")

    finally:
        if driver:
            try:
                time.sleep(2)
                driver.close()
                time.sleep(1)
                driver.quit()
                logger.info("Driver successfully closed")
            except Exception as e:
                logger.error(f"Error while closing the driver: {e}")
        logger.info("=== Parsing process finished ===")


if __name__ == "__main__":
    main()
