import os
import re
import time
from urllib import parse as urlparse

from selenium import webdriver

import config

browser = webdriver.Chrome()


def login():
    browser.get(config.AMAZON_LOGIN_URL)
    time.sleep(5)

    # Fill username
    email = browser.find_element_by_name("email")
    email.send_keys(config.AMAZON_USER_EMAIL)
    email.submit()
    time.sleep(5)

    # Fill password
    password = browser.find_element_by_name("password")
    password.send_keys(config.AMAZON_USER_PASSWORD)
    password.submit()
    time.sleep(45)


def download_invoices_with_tracking_ids_as_pdf():
    login()

    browser.get(config.AMAZON_ORDERS_URL)
    time.sleep(5)
    order_urls_length = len(browser.find_elements_by_xpath("//a[contains(@href, 'progress-tracker')]"))

    if not order_urls_length:
        browser.quit()

    orders = []

    for i in range(order_urls_length):
        order_url = browser.find_elements_by_xpath("//a[contains(@href, 'progress-tracker')]")[i]
        order_url.click()
        time.sleep(5)
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
        browser.implicitly_wait(5)

    here = os.path.dirname(os.path.abspath(__file__))
    download_folder = f'{here}/Downloads'

    if not os.path.exists(download_folder):
        os.mkdir(f'{here}/Downloads')

    for i in range(order_urls_length):
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
    download_invoices_with_tracking_ids_as_pdf()
