import requests
import time
import random
from bs4 import BeautifulSoup
import pandas as pd
import logging


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
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


# Logger configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(CustomFormatter())
logger.addHandler(console_handler)


def scrape_data(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Product title
        title_tag = soup.select_one("h1.font-oswald.text-3xl.font-bold")
        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        # Article number
        stock_number_tag = soup.select_one('[data-testid="stock-number-desktop"] + dd')
        stock_number = (
            stock_number_tag.get_text(strip=True) if stock_number_tag else "N/A"
        )

        # Part number
        part_number_tag = soup.select_one('[data-testid="mpn-desktop"] + dd')
        part_number = part_number_tag.get_text(strip=True) if part_number_tag else "N/A"

        # Manufacturer
        brand_tag = soup.select_one('[data-testid="brand-desktop"] + dd')
        brand = brand_tag.get_text(strip=True) if brand_tag else "N/A"

        # Price without VAT
        price_exc_vat_tag = soup.select_one('[data-testid="price-exc-vat"]')
        price_exc_vat = (
            price_exc_vat_tag.get_text(strip=True) if price_exc_vat_tag else "N/A"
        )

        # Price with VAT
        price_inc_vat_tag = soup.select_one('[data-testid="price-inc-vat"]')
        price_inc_vat = (
            price_inc_vat_tag.get_text(strip=True) if price_inc_vat_tag else "N/A"
        )

        # Documentation links
        document_links = []
        doc_tags = soup.select('[data-testid="technical-documents"] a')
        for tag in doc_tags:
            doc_url = tag["href"]
            doc_name = tag.get_text(strip=True)
            document_links.append(f"{doc_name}: {doc_url}")

        return {
            "Name": title,
            "Art.": stock_number,
            "Part number": part_number,
            "Manufacturer": brand,
            "Price without VAT": price_exc_vat,
            "Price with VAT": price_inc_vat,
            "Documentation": "\n".join(document_links),
        }

    except requests.RequestException as e:
        logger.error(f"Error during request {url}: {e}")
        return None


# Function to load collected links
def load_links(file_path="rsonline_collected_links.txt"):
    with open(file_path, "r") as file:
        return [line.strip() for line in file.readlines() if line.strip()]


# Main function
def main():
    logger.info("=== Starting Scraping Process ===")
    links = load_links()
    logger.info(f"Found {len(links)} links to process.")

    all_data = []
    for idx, link in enumerate(links, start=1):
        time.sleep(random.uniform(2, 5))
        logger.info(f"({idx}/{len(links)}) Processing: {link}")
        data = scrape_data(link)
        if data:
            all_data.append(data)

    # Save data to Excel file
    df = pd.DataFrame(all_data)
    df.to_excel("rsonline_data.xlsx", index=False)
    logger.info("Data saved to rsonline_data.xlsx.")
    logger.info("=== Scraping Process Finished ===")


if __name__ == "__main__":
    main()
