from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from amazoncaptcha import AmazonCaptcha
import time
import openpyxl
from sqlalchemy import text
from sqlalchemy import engine
import psycopg2
import os


class AmazonScraper:
    def __init__(self):
        self.url = 'https://www.amazon.com/'
    
    def find_captcha(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        result = soup.find('div', class_='a-row a-text-center').find('img').get('src')
        return result
    
    def extract_search_items(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        page_results = soup.find_all('div', {'data-component-type': 's-search-result'})
        return page_results
    
    def get_max_page(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        max_page = soup.find('span', class_='s-pagination-item s-pagination-disabled')
        
        if max_page is not None:
            return int(max_page.text)
        
        button_pagination = soup.find_all('a', class_='s-pagination-item s-pagination-button')
        
        if len(button_pagination) == 0:
            return 1

        max_page = button_pagination[-1].text

        return int(max_page)
    
    def parsing_product_item(self, page_results):
        results = []

        for item in page_results:
            sponsor_tag = item.find('span', class_='aok-inline-block puis-sponsored-label-info-icon')
            if sponsor_tag:
                print('skip sponsored item')
                continue

            a_tag  = item.find('a', class_='a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal')
            title = a_tag.text.strip()
            # brand = item.find('span', class_='a-size-medium a-color-base').text if item.find('span', class_='a-size-medium a-color-base') else 'None'
            url_product = f'https://www.amazon.com{a_tag.get("href")}'
            thumbnail_link = item.find('img', class_='s-image').get('src')
            rating = float(item.find('span', class_='a-icon-alt').text.replace(' out of 5 stars', '')) if item.find('span', class_='a-icon-alt') else None
            price_whole = item.find('span', class_='a-price-whole').text.replace(',', '') if item.find('span', class_='a-price-whole') else None
            price_fraction = item.find('span', class_='a-price-fraction').text if item.find('span', class_='a-price-fraction') else None
            product_price = float(f'{price_whole}{price_fraction}') if price_whole and price_fraction else None

            product = {
                'title': title,
                'thumbnail_link': thumbnail_link,
                'url': url_product,
                'rating': rating,
                'price_in_usd': product_price
            }

            results.append(product)
        
        return results

    def input_to_xlsx(self, parsed_products, file_name):
        wb = openpyxl.Workbook()
        ws = wb.active

        for i in range(len(parsed_products)):
            if i == 0:
                ws.append(list(parsed_products[i].keys()))
                ws.append(list(parsed_products[i].values()))
            else:
                ws.append(list(parsed_products[i].values()))

        
        wb.save(file_name)


    def input_to_postgresdb(self, parsed_products):
        try:
            global engine

            POSTGRES_USER = os.environ.get('POSTGRES_USER')
            POSTGRES_DB = os.environ.get('POSTGRES_DB')
            POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')

            engine = engine.create_engine(f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}')

            global conn
            conn = engine.connect()
            
            query = text('CREATE TABLE IF NOT EXISTS products (id SERIAL PRIMARY KEY, title VARCHAR(500), thumbnail_link VARCHAR(500), url VARCHAR(500), rating NUMERIC(2,1), price_in_usd NUMERIC(10,2));') 
            conn.execute(query)
            conn.commit()
    
            for item in parsed_products:
                stmt = text("INSERT INTO products (title, thumbnail_link, url, rating, price_in_usd) VALUES (:title, :thumbnail_link, :url, :rating, :price_in_usd)")
                conn.execute(stmt, item)
            
            conn.commit()
            
            conn.close()

        except Exception as e:
            print("Error while connecting to PostgreSQL:", e)
            

    def run(self, keywords, file_name):

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()
            page.goto(self.url)

            captcha_url = self.find_captcha(page.content())
            if captcha_url is not None:
                captcha = AmazonCaptcha.fromlink(captcha_url)
                solution = captcha.solve()
                page.get_by_placeholder('Type characters').fill(str(solution))
                page.get_by_text('Continue shopping').click()

            time.sleep(3)
            keywords = keywords.replace(' ', '+')
            page.goto(f'{self.url}/s?k={keywords}')
            time.sleep(3)
            max_page = self.get_max_page(page.content())
            print("Max page is " + str(max_page))

            result = []

            result_page_1 = self.extract_search_items(page.content())
            print('Extracted items on page 1', len(result_page_1))
            result += result_page_1

            for i in range(2, max_page + 1):
                page.goto(f'{self.url}/s?k={keywords}&page={i}')
                time.sleep(3)
                result_page = self.extract_search_items(page.content())
                print('Extracted items on page ' + str(i), len(result_page))
                result += result_page
    
            parsed_products = self.parsing_product_item(result)
            self.input_to_xlsx(parsed_products, file_name)
            self.input_to_postgresdb(parsed_products)















