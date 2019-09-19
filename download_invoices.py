import os
import re
import time
from urllib import parse as urlparse

from selenium import webdriver

import config

browser = webdriver.Chrome()


def login():
    browser.get(config.AMAZON_LOGIN_URL)
    time.sleep(2)

    # Fill username
    email = browser.find_element_by_name("email")
    email.send_keys(config.AMAZON_USER_EMAIL)
    email.submit()
    time.sleep(2)

    # Fill password
    password = browser.find_element_by_name("password")
    password.send_keys(config.AMAZON_USER_PASSWORD)
    password.submit()
    time.sleep(15)


def download_invoices_with_tracking_ids_as_pdf():
    login()

    browser.get(config.AMAZON_ORDERS_URL)
    time.sleep(2)
    tracking_urls_length = len(browser.find_elements_by_xpath("//a[contains(@href, 'progress-tracker')]"))

    tracking_numbers = []

    for i in range(tracking_urls_length):
        tracking_url = browser.find_elements_by_xpath("//a[contains(@href, 'progress-tracker')]")[i]
        tracking_url.click()
        time.sleep(2)
        current_url = browser.current_url
        parsed = urlparse.urlparse(current_url)
        order_id = urlparse.parse_qs(parsed.query)["orderId"][0]
        tracking_id = browser.find_element_by_partial_link_text("Tracking").text.split(" ")[-1]
        tracking_numbers.append({order_id: tracking_id})
        browser.back()
        browser.implicitly_wait(2)

    here = os.path.dirname(os.path.abspath(__file__))
    download_folder = f'{here}/Downloads'
    if not os.path.exists(download_folder):
        os.mkdir(f'{here}/Downloads')

    for i in range(tracking_urls_length):
        order_id = list(tracking_numbers[i].keys())[0]
        tracking_id = list(tracking_numbers[i].values())[0]
        html_file = f'{here}/Downloads/invoice_{order_id}.html'
        browser.get(config.AMAZON_ORDER_INVOICE_URL + order_id)

        with open(html_file, 'wb') as f:
            page_content = browser.page_source
            page_content_encoded = page_content.replace(
                re.findall(
                    f'{order_id}', page_content)[0], f"{order_id} Tracking ID: {tracking_id}"
            ).encode('utf-8')
            f.write(page_content_encoded)


if __name__ == '__main__':
    download_invoices_with_tracking_ids_as_pdf()
