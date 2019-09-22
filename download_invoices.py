import argparse
import os
import re
import time
from urllib import parse as urlparse

from selenium import webdriver

import config


def login():
    browser.get(config.AMAZON_LOGIN_URL)
    time.sleep(config.WAITING_TIME_BETWEEN_PAGES)

    # Fill username
    email = browser.find_element_by_name("email")
    email.send_keys(config.AMAZON_USER_EMAIL)
    email.submit()
    time.sleep(config.WAITING_TIME_BETWEEN_PAGES)

    # Fill password
    password = browser.find_element_by_name("password")
    password.send_keys(config.AMAZON_USER_PASSWORD)
    password.submit()
    time.sleep(config.WAITING_TIME_AFTER_LOGIN)


def download_invoices_with_tracking_ids_as_pdf(amount_of_invoices):
    login()

    browser.get(config.AMAZON_ORDERS_URL)
    time.sleep(config.WAITING_TIME_BETWEEN_PAGES)

    order_urls_length = len(browser.find_elements_by_xpath("//a[contains(@href, 'progress-tracker')]"))

    if not order_urls_length:
        browser.quit()

    # Check if the given input to download invoices is equal or less than total orders. If not, download all orders.
    if 0 < amount_of_invoices <= order_urls_length:
        total_invoices_to_download = amount_of_invoices
    else:
        total_invoices_to_download = order_urls_length

    orders = []

    for i in range(total_invoices_to_download):
        order_url = browser.find_elements_by_xpath("//a[contains(@href, 'progress-tracker')]")[i]
        order_url.click()
        time.sleep(config.WAITING_TIME_BETWEEN_PAGES)
        current_url = browser.current_url
        parsed = urlparse.urlparse(current_url)
        order_id = urlparse.parse_qs(parsed.query)["orderId"][0]

        try:
            tracking_id = browser.find_element_by_partial_link_text("Tracking").text.split(" ")[-1]
        except Exception:
            tracking_id = ""

        try:
            # Amazon.com shows delivery company with "Shipped with" sentence.
            delivery_by = browser.find_elements_by_xpath("//*[contains(text(), 'Shipped with')]")[0].text
        except Exception:
            delivery_by = ""

        if not delivery_by:
            try:
                # Some other amazon websites like amazon.de shows delivery company with "Delivery By" sentence.
                delivery_by = browser.find_elements_by_xpath("//*[contains(text(), 'Delivery By')]")[0].text
            except Exception:
                delivery_by = ""

        orders.append({order_id: {"tracking_id": tracking_id, "delivery_by": delivery_by}})

        browser.back()
        browser.implicitly_wait(config.WAITING_TIME_BETWEEN_PAGES)

    here = os.path.dirname(os.path.abspath(__file__))
    download_folder = f'{here}/Downloads'

    if not os.path.exists(download_folder):
        os.mkdir(f'{here}/Downloads')

    for i in range(total_invoices_to_download):
        order_id = list(orders[i].keys())[0]
        tracking_id = orders[i][order_id]["tracking_id"]
        delivery_by = orders[i][order_id]["delivery_by"]
        html_file = f'{here}/Downloads/invoice_{order_id}.html'

        browser.get(config.AMAZON_ORDER_INVOICE_URL + order_id)

        with open(html_file, 'wb') as f:
            page_content = browser.page_source
            page_content_encoded = page_content.replace(
                re.findall(
                    f'{order_id}', page_content)[0], f"{order_id} Tracking ID: {tracking_id} {delivery_by}",
            ).encode('utf-8')
            f.write(page_content_encoded)

    browser.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoices_amount", type=int, default=0, help="Amount of invoices to be downloaded.")
    args = parser.parse_args()

    browser = webdriver.Chrome()

    download_invoices_with_tracking_ids_as_pdf(args.invoices_amount)
