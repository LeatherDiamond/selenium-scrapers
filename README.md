# Navigation
* ***[Project description](#project-description)***
* ***[Key features](#key-features)***
* ***[Technical stack](#technical-stack)***
* ***[Code formatting and quality checking tools](#code-formatting-and-quality-checking-tools)***
* ***[How to start](#how-to-start)***
* ***[Licence](#licence)***

# Project description

This project is a collection of web scrapers designed to extract product data from various electronic component distributor websites. Each scraper is specifically tailored to navigate and parse the unique structure of its target site, ensuring reliable and efficient data collection. The scrapers are capable of handling both static and dynamic content, making use of advanced techniques to bypass common anti-scraping measures. The primary workflow involves collecting product links from listing pages and then scraping detailed information such as pricing, stock levels, and documentation from individual product pages.

# Key features

- **Modular Architecture**: Each scraper operates independently, allowing for easy maintenance, updates, and the addition of new scrapers for different websites.
- **Dynamic Content Handling**: Leverages Selenium and Pyppeteer to interact with JavaScript-heavy websites, ensuring accurate extraction of dynamically loaded data.
- **Anti-Bot Evasion**: Implements sophisticated strategies, including human-like mouse movements, smooth scrolling, and randomized delays, to avoid detection and blocking by target websites.
- **Detailed Data Extraction**: Collects comprehensive product information, including titles, part numbers, prices, stock quantities, and documentation links (e.g., datasheets).
- **Custom Logging**: Features color-coded logs for improved readability and streamlined debugging during scraping operations.
- **Session Management**: Utilizes cookie storage to maintain session states across multiple scraping runs, enhancing efficiency and consistency.
- **Data Export**: Processes collected data and exports it to Excel files for easy analysis and sharing.

# Technical stack

The project is built using the following technologies:

- **Python 3.x**: The core programming language driving all scraping logic and data processing.
- **Selenium with undetected_chromedriver**: Provides browser automation for scraping dynamic content while evading detection mechanisms.
- **Pyppeteer**: Offers asynchronous control of headless browsers, ideal for efficient handling of JavaScript-rendered pages.
- **BeautifulSoup4**: Used for parsing and navigating HTML content in scenarios where static HTML scraping is sufficient.
- **Pandas**: Facilitates data manipulation and exporting scraped data to Excel files.
- **asyncio**: Manages asynchronous operations, particularly with Pyppeteer, to optimize performance.
- **python-dotenv**: Securely manages environment variables, such as executable paths and proxy settings.
- **Logging**: Custom-configured with color-coded console output for real-time monitoring and debugging.
- **Proxy Support**: Optional integration of proxies to enhance anonymity and circumvent IP-based restrictions.

# Code formatting and quality checking tools
> ###### **NOTE:**
> Note, that for the current version of code `black` and `flake8` have already been applied. For further code development, please follow the steps described below to ensure high-quality code.

1. Run `poetry shell` to activate environment if it's not active yet;
2. Run `black . --check` to check if the code needs to be reformatted;
3. Run `black .` to reformat the code;
4. Run `flake8` to identify potential issues, such as syntax errors, code style violations, and other coding inconsistencies during the development process;

# How to start

**1. Clone current repository on your local machine:**
```

```

**2. Activate virtual environment in the root directory of the project:**
```
poetry shell
```

**3. Install all the dependencies for the project:**
```
poetry install --no-root
```

**4. Configure `.env` file by assigning values to the variables defined in `env.sample`**

**5. Run necessary script and wait untill the process is completed.**
```
python farnell_links_collect.py
```
> ###### **NOTE:**
> Note that collecting information for some websites in these examples works in two steps. This means you need to run one script to collect the necessary links, and after it has completed, run 
> a second script to process each link and retrieve the necessary information.

# Licence

**This project is licensed under the Apache-2.0 license - see the [LICENSE]() file for details.**