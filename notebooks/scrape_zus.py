import os
import re
import time
import csv
import sqlite3
from typing import Optional
from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import logging

@dataclass
class GMapDetails:
    name: str = ""
    address: str = ""
    phone_number: str = ""
    reviews_count: Optional[int] = None
    reviews_average: Optional[float] = None
    services: str = ""
    place_type: str = ""
    opens_at: str = ""

class ZUSScraper:
    def __init__(self, headless=True, base_delay=2):
        """
        Initialize ZUS Scraper
        
        Args:
            headless (bool): Run browser in headless mode
            base_delay (int): Base delay between actions in seconds
        """
        self.base_delay = base_delay
        self.driver = None
        self.setup_driver(headless)
        self.save_path = "data"
        os.makedirs(self.save_path, exist_ok=True)
        
    def setup_driver(self, headless=True):
        """Setup Chrome driver with options"""
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=options)
        
    def scrape_products(self, product_scrape: bool = False, to_sql: bool = False):
        """Scrape ZUS drinkware products"""
        BASE_URL = "https://shop.zuscoffee.com"

        # === Step 1: Go to main page and click Drinkware tab ===
        if product_scrape:
            self.driver.get(BASE_URL)
            time.sleep(self.base_delay)

            button = self.driver.find_element(By.XPATH, "/html/body/main/div[1]/div/div/x-tabs/button[2]")
            button.click()
            # print(button.text)

            # Extract product links from the correct tab
            time.sleep(self.base_delay)

            # # === Step 2: Collect product links ===
            tab = self.driver.find_element(By.CSS_SELECTOR, 'div.tab-content[style="opacity: 1;"]')

            # === Step 3: Scrape product info ===
            sections_titles = tab.find_elements(By.XPATH, "./div[contains(@class, 'bl_custom_collections_list-collection_title')]")
            sections_wrappers = tab.find_elements(By.XPATH, "./div[contains(@class, 'bl_custom_collections_list-collection_wrapper')]")
            
            categories_titles = [section.text.strip() for section in sections_titles]
            print(f"Found {len(categories_titles)} categories.")

            categories_dict = {} 

            for i, category in enumerate(categories_titles):
                try:
                    product_links = [
                        a.get_attribute("href")
                        for a in sections_wrappers[i].find_elements(By.CSS_SELECTOR, ".product-card__figure a")
                        if a.get_attribute("href")
                    ]
                    categories_dict[category] = product_links
                except Exception as e:
                    print(f"Failed to fetch product links for category '{category}': {e}")
                    categories_dict[category] = []
            
            products=[]

            for category, product_links in categories_dict.items():
                for url in product_links:
                    product_data = []
                    self.driver.get(url)
                    time.sleep(self.base_delay)

                    try:
                        name = self.driver.find_element(By.CSS_SELECTOR, "h1.product-info__title").text
                        image = self.driver.find_element(By.CSS_SELECTOR, ".product-gallery__media.is-selected img[src*='files/']").get_attribute("src")
                        price_text = self.driver.find_element(By.CSS_SELECTOR, "sale-price.text-lg").text
                        price = float(re.search(r"\d+\.\d{2}", price_text).group())

                        try:
                            color_labels = self.driver.find_elements(By.CSS_SELECTOR, "label.thumbnail-swatch .sr-only")
                            colors = [label.text.strip() for label in color_labels  if len(label.text.strip()) > 2]
                        except Exception as e:
                            print("Color variants not found:", e)
                        try:
                            summary = self.driver.find_element(By.CSS_SELECTOR, "details.product-info__accordion > summary")
                            self.driver.execute_script("arguments[0].click();", summary)
                            time.sleep(1)
                        except Exception as e:
                            print("Failed to expand accordion:", e)
                        try:
                            description_element = self.driver.find_element(By.CSS_SELECTOR, ".accordion__content .prose")
                            description = description_element.text.strip()
                        except Exception as e:
                            print("Description not found:", e)
                    except Exception as e:
                        print(f"Error parsing product {url}: {e}")
                        continue

                    color_str = ", ".join(colors)
                    product_data = [category, name, image, color_str, price, description]
                    products.append(product_data)
                    self.save_data_to_csv("zus_products.csv", product_data, ['category_title', 'name', 'image', 'color', 'price', 'description'])

        # === Step 4: Save to SQL ===
        if to_sql:
            df = pd.read_csv(os.path.join(self.save_path, "zus_products.csv"), encoding='utf-8-sig')
            products = df.to_dict(orient='records')
            print(products)
            self.save_products_to_sql(products)
            print(f"Product scraping complete. SQL written to {self.save_path}/zus_products.sql")
        else:
            print("Products scraped to csv file.")
        
    def save_products_to_sql(self, products):
        """Save products to SQL file"""
        with open(os.path.join(self.save_path, "zus_products.sql"), "w", encoding="utf-8") as f:
            f.write("CREATE TABLE products (id INTEGER PRIMARY KEY, category_title TEXT, name TEXT, image TEXT, color TEXT, price DECIMAL(10, 2), description TEXT);\n")
            for i, row in enumerate(products):
                id = i + 1

                # Escape and format fields safely
                def esc(val):
                    return str(val or "").replace("'", "''")
                
                f.write(
                    f"INSERT INTO products VALUES ({id}, "
                    f"'{esc(row.get('category_title'))}', "
                    f"'{esc(row.get('name'))}', "
                    f"'{esc(row.get('image'))}', "
                    f"'{esc(row.get('color'))}', "
                    f"{row.get('price')}, "
                    f"'{esc(row.get('description'))}');\n"
                )


    def save_data_to_csv(self, filepath, data: list, header: list):
        csv_file_path = os.path.join(self.save_path, filepath)
        file_exists = os.path.exists(csv_file_path)  # Check BEFORE opening

        with open(csv_file_path, 'a' if file_exists else 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)

            if not file_exists:
                csv_writer.writerow(header)  # Write header row only once
                print("CSV header written.")
            else:
                print("CSV header already exists, skipping header write.")

            csv_writer.writerow(data)  # Write scraped data

    def extract_data_from_zus_website(self, zus_url: str) -> Optional[str]:
        for attempt in range(3):
            try:
                # Navigate to the website
                self.driver.get(zus_url)

                # Wait for the main container that holds the outlet posts to be present
                # Increased wait time for live website to load content
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.elementor-posts-container'))
                )

                container = self.driver.find_element(By.CSS_SELECTOR, 'div.elementor-posts-container')
                # print(container.get_attribute("outerHTML"))

                # Find all outlet elements (each block representing a outlet)
                outlet_elements = container.find_elements(By.CSS_SELECTOR, 'article.elementor-post')
                print(f"Found {len(outlet_elements)} outlets.")

                scraped_data = []

                for i, outlet_el in enumerate(outlet_elements):
                    outlet_name = ""
                    outlet_address = ""
                    outlet_link = ""
                    
                    try:
                        outlet_name_address = outlet_el.find_elements(By.CSS_SELECTOR, '.elementor-widget-container p')
                        outlet_name = outlet_name_address[0].text.strip().replace('\n', '')
                        # print(f"Outlet name: {outlet_name}")
                        outlet_address = outlet_name_address[1].text.strip().replace('\n', '')
                        # print(f"Outlet address: {outlet_address}")
                    except Exception as e:
                        print(f"Error parsing outlet {i}: {e}")
                        outlet_name=""
                        outlet_address=""
                    try:
                        outlet_link = outlet_el.find_element(By.CSS_SELECTOR, 'a.premium-button-none.premium-btn-lg[target="_blank"]').get_attribute("href")
                    except Exception as e:
                        print(f"Error parsing outlet {i}: {e}")
                        outlet_link="" 
                    if outlet_name:
                        scraped_data.append([outlet_name, outlet_address, outlet_link])

                csv_file_path = os.path.join(self.save_path, "zus_outlets.csv")
                file_exists = os.path.exists(csv_file_path)  # Check BEFORE opening

                with open(csv_file_path, 'a' if file_exists else 'w', newline='', encoding='utf-8') as csvfile:
                    csv_writer = csv.writer(csvfile)

                    if not file_exists:
                        csv_writer.writerow(['name', 'address', 'link'])  # Write header row only once
                        print("CSV header written.")
                    else:
                        print("CSV header already exists, skipping header write.")

                    csv_writer.writerows(scraped_data)  # Write scraped data

                print(f"Scraping complete! Data saved to '{csv_file_path}'")
                print(f"Total outlets scraped: {len(scraped_data)}")

                return csv_file_path

            except Exception as e:
                print(f"An unexpected error occurred during scraping: {e}")
                return None

    def extract_gmap_details(self, gmap_url: str) -> GMapDetails:
        print("Processing outlet link: ", gmap_url)
        for attempt in range(3):
            try:
                self.driver.get(gmap_url)
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "t39EBf")]'))
                )
            except Exception as e:
                try:
                    container = self.driver.find_element(By.XPATH, "//div[contains(@class, 't39EBf')]")
                except Exception as e:
                    print("outlet link not found: ", gmap_url)
                    return None
            else:
                def safe_find(selector):    
                    try:
                        return self.driver.find_element(By.XPATH, selector).text.strip()
                    except:
                        return ""
                elements = self.driver.find_elements(By.XPATH, '//div[@class="LTs0Rc"]/div[@aria-hidden="true"]')
                text_list = [el.text.strip() for el in elements if el.text.strip()]
                # print(text_list)
                services_list = ", ".join(text_list)
                services_list = services_list.replace("", "")

                input_hours = []

                try:
                    container = self.driver.find_element(By.XPATH, "//div[contains(@class, 't39EBf')]")
                    rows = container.find_elements(By.XPATH, ".//table[contains(@class, 'eK4R0e')]//tr[contains(@class, 'y0skZc')]")
                    for row in rows:
                        try:
                            # Extract day and time
                            # print(row.get_attribute("outerHTML")) 
                            tr = row.find_element(By.XPATH, './/button[contains(@class, "mWUh3d")]')
                            data_value = tr.get_attribute("data-value").replace("\u202f","")
                            input_hours.append(f"{data_value}")
                        except Exception as e:
                            print(f"Error parsing row: {e}")
                except Exception as e:
                    print(f"Error extracting operating hours: {e}")
                
                days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_to_order = {day: i for i, day in enumerate(days_order)}

                def get_day_order(item):
                    # Extract the day name from the string (e.g., 'Wednesday' from 'Wednesday, 8am–9:40pm')
                    day_name = item.split(',')[0].strip()
                    # Return its numerical order
                    return day_to_order.get(day_name)

                # Sort the input_hours list using the custom key
                input_hours = sorted(input_hours, key=get_day_order)
                opens_at = ', '.join(input_hours)
                # print("input_hours", input_hours)

                gmap = GMapDetails(
                    address=safe_find('//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'),
                    phone_number=safe_find('//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'),
                    reviews_count=safe_find('//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span//span//span[@aria-label]'),
                    reviews_average=safe_find('//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span[@aria-hidden]'),
                    services=services_list,
                    place_type=safe_find('//div[@class="LBgpqf"]//button[@class="DkEaL "]'),
                    opens_at=opens_at,
                )


                reviews_count_raw = safe_find('//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span//span//span[@aria-label]')
                if reviews_count_raw:
                    try:
                        temp = reviews_count_raw.replace('\xa0', '').replace('(','').replace(')','').replace(',','')
                        gmap.reviews_count = int(temp)
                    except Exception as e:
                        logging.warning(f"Failed to parse reviews count: {e}")

                reviews_avg_raw = safe_find('//div[@class="TIHn2 "]//div[@class="fontBodyMedium dmRWX"]//div//span[@aria-hidden]')
                if reviews_avg_raw:
                    try:
                        temp = reviews_avg_raw.replace(' ','').replace(',','.')
                        gmap.reviews_average = float(temp)
                    except Exception as e:
                        logging.warning(f"Failed to parse reviews average: {e}")

                return gmap

    def scrape_outlets(self, page_range: tuple[int, int]=None, gmap_scrape: list=None, to_sql: bool = False):
        """Scrape ZUS outlets"""
        filename = "zus_outlets.csv"
        file_path = os.path.join(self.save_path, filename)
        if not os.path.exists(file_path) or page_range is not None:
            failed_pages = []
            BASE_URL = "https://zuscoffee.com/category/outlet/kuala-lumpur-selangor/page/"
            for page in range(page_range[0], page_range[1]):  # Pages 1 to 22
                print(f"Scraping Page {page}...")
                file_path = self.extract_data_from_zus_website(BASE_URL + str(page))
                if file_path is None:
                    failed_pages.append(page)
            print(f"Failed pages: {failed_pages}")

        if gmap_scrape is not None:
            expanded_outlets_data = []
            failed_urls = []
            failed_urls_index = []            

            outlets_name_list = gmap_scrape['name'].tolist()
            outlets_address_list = gmap_scrape['address'].tolist()
            outlets_gmap_list = gmap_scrape['link'].tolist()
            

            # Loop through each outlet
            for index, link in enumerate(outlets_gmap_list):
                name = outlets_name_list[index]
                original_address = outlets_address_list[index]
                outlet_link = link

                print(f"\nProcessing outlet id: {id} - Name: {name}")

                # Scrape Google Maps details
                details = self.extract_gmap_details(outlet_link)

                if details is None:
                    print(f"  Failed to get Google Maps details for {name}. Using original data.")
                    expanded_row = [
                        name, original_address, outlet_link,
                        'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'
                    ]
                    failed_urls.append(outlet_link)
                    failed_urls_index.append(index)
                else:
                    # Heuristic to check garbled or missing address
                    replace_address = False
                    if '�' in original_address or len(original_address) < 10:
                        print(f"  Original address seems garbled: '{original_address}'. Replacing with GMap address.")
                        replace_address = True
                    elif original_address == "N/A" and details.address != "N/A":
                        print(f"  Original address is 'N/A'. Replacing with GMap address.")
                        replace_address = True

                    final_address = details.address if replace_address else original_address
                    expanded_row = [
                        name,
                        final_address,
                        outlet_link,
                        details.reviews_count if details.reviews_count else 'N/A',
                        details.reviews_average if details.reviews_average else 'N/A',
                        details.phone_number if details.phone_number else 'N/A',
                        details.services if details.services else 'N/A',
                        details.place_type if details.place_type else 'N/A',
                        details.opens_at if details.opens_at else 'N/A'
                    ]

                self.save_data_to_csv("zus_outlets_final.csv", expanded_row, ['name', 'address', 'link', 'reviews_count', 'reviews_average', 'phone_number', 'services', 'place_type', 'opens_at'])
            print('Failed urls: ', failed_urls, '\n',
                    'Failed urls index: ', failed_urls_index)
            return failed_urls
        
        if to_sql:
            csv_path = os.path.join(self.save_path, "zus_outlets_final.csv")
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            expanded_outlets_data = df.to_dict(orient='records')
            self.save_outlets_to_sql(expanded_outlets_data)
            print(f"Outlet scraping complete. SQL written to {self.save_path}/zus_outlets.sql")
        else:
            print("Outlets from zus website scraped to csv file.")

    def save_outlets_to_sql(self, outlets):
        """Save outlet rows to an SQL file from iterable of dicts (e.g. csv.DictReader)"""
        with open(os.path.join(self.save_path, "zus_outlets.sql"), "w", encoding="utf-8") as f:
            f.write("CREATE TABLE outlets (id INTEGER PRIMARY KEY, name TEXT, address TEXT, link TEXT, reviews_count INTEGER, reviews_average FLOAT, phone_number TEXT, services TEXT, place_type TEXT, opens_at TEXT);\n")

            for i, row in enumerate(outlets):
                id = i + 1

                # Escape and format fields safely
                def esc(val):
                    return str(val or "").replace("'", "''")

                f.write(
                    f"INSERT INTO outlets VALUES ({id}, "
                    f"'{esc(row.get('name'))}', "
                    f"'{esc(row.get('address'))}', "
                    f"'{esc(row.get('link'))}', "
                    f"{int(row.get('reviews_count', 0))}, "
                    f"{row.get('reviews_average', 0.0)}, "
                    f"'{esc(row.get('phone_number'))}', "
                    f"'{esc(row.get('services'))}', "
                    f"'{esc(row.get('place_type'))}', "
                    f"'{esc(row.get('opens_at'))}');\n"
                )



    def close(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            
    def __enter__(self):
        """Context manager entry"""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


if __name__ == "__main__":
    # Example usage
    with ZUSScraper(headless=True, base_delay=2) as scraper:
        # Scrape products
        scraper.scrape_products(product_scrape=False, to_sql=True)
        
        # Scrape outlets
        # scraper.scrape_outlets(to_sql=False, gmap_scrape=True)