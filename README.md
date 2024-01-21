# Amazon Scraper

## Objective
Scraping items on amazon search page
![search page](/readmeimg/search_page.png)

## Requirements
- BeautifulSoup4
- Playwright
- AmazonCaptcha
- Openpyxl
- SQLAlchemy and psycopg2

## Features
- Scraping product title, price, rating, thumbnail link, and product link
- Solving Captcha automatically using AmazonCaptcha and Playwright
- Inputing scraped data to xlsx file
- Inputting scraped data to PostgreSQL database