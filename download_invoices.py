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


def get_tracking_id():
    """

    :return: tracking_id
    """
    try:
        tracking_id = browser.find_element_by_partial_link_text("Tracking").text.split(" ")[-1]
    except Exception:
        tracking_id = ""

    return tracking_id


def get_delivery_company():
    """

    :return: delivery_by: name of the delivery company
    """
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

    return delivery_by


def get_ordered_item_names():
    """

    :return: item_names: all items which are belong to same progress tracker
    """
    length_of_items = len(browser.find_elements_by_xpath("//a[contains(@href, 'gp/product')]"))
    item_names = []
    for i in range(length_of_items):
        item_url = browser.find_elements_by_xpath("//a[contains(@href, 'gp/product')]")[i]
        item_url.click()
        time.sleep(config.WAITING_TIME_BETWEEN_PAGES)
        item_names.append(browser.title)
        browser.back()
        time.sleep(config.WAITING_TIME_BETWEEN_PAGES)

    return item_names


def get_all_orders_with_tracking_info(amount_of_invoices):
    """

    :param amount_of_invoices: Amount of the invoices to gather the info
    :return: orders: all orders as list of order ids which have the list of tracking information with tracking_id,
    name of the delivery company and ordered items which belong to that specific tracking_id.
    """
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
        # Click progress tracker of the order and go to that page.
        progress_tracker = browser.find_elements_by_xpath("//a[contains(@href, 'progress-tracker')]")[i]
        progress_tracker.click()
        time.sleep(config.WAITING_TIME_BETWEEN_PAGES)

        # Get the order id from the URL of the progress tracker
        current_url = browser.current_url
        parsed = urlparse.urlparse(current_url)
        order_id = urlparse.parse_qs(parsed.query)["orderId"][0]

        # Collect tracking id, delivery company and name of the items which are tracked in the progress tracker.
        tracked_item = {
            "tracking_id": get_tracking_id(),
            "delivery_by": get_delivery_company(),
            "item_names": get_ordered_item_names()
        }

        # If order_id already exists, that means there are multiple tracking for the same order with different items.
        # So, extend same order_id with new tracked_item. Else, add order_id with tracked_item as it's not existing yet.
        if any(order_id in order for order in orders):
            for order in orders:
                if order_id in order:
                    index = orders.index(order)
                    orders[index][order_id].append(tracked_item)
        else:
            orders.append({order_id: [tracked_item]})

        # Go back orders page to continue with clicking progress tracker pages.
        browser.get(config.AMAZON_ORDERS_URL)
        browser.implicitly_wait(config.WAITING_TIME_BETWEEN_PAGES)

    return orders


def download_invoices_with_tracking_ids_as_pdf(amount_of_invoices):
    """
    Downloads the invoices with order ids, tracking ids, delivery company name and
    ordered items belong to specific tracking id.
    """
    orders_with_tracking_info = get_all_orders_with_tracking_info(amount_of_invoices)

    here = os.path.dirname(os.path.abspath(__file__))
    download_folder = f'{here}/Downloads'

    if not os.path.exists(download_folder):
        os.mkdir(f'{here}/Downloads')

    for i in range(len(orders_with_tracking_info)):
        order_id = list(orders_with_tracking_info[i].keys())[0]

        for order in orders_with_tracking_info[i][order_id]:
            tracking_id = order["tracking_id"]
            delivery_by = order["delivery_by"]
            items = order["item_names"]
            order_number = orders_with_tracking_info[i][order_id].index(order) + 1
            html_file = f'{here}/Downloads/invoice_{order_id}_{order_number}.html'

            browser.get(config.AMAZON_ORDER_INVOICE_URL + order_id)
            items_as_html = ', <br /> '.join(items)

            with open(html_file, 'wb') as f:
                page_content = browser.page_source
                page_content_encoded = page_content.replace(
                    re.findall(
                        f'{order_id}', page_content)[0], f"{order_id} <br /> "
                                                         f"<b>Tracking ID</b>: {tracking_id} <br /> "
                                                         f"<b>{delivery_by}</b> <br /> "
                                                         f"<b><u>ORDERED ITEMS:</b></u> <br /> {items_as_html}",
                ).encode('utf-8')
                f.write(page_content_encoded)

    browser.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoices_amount", type=int, default=0, help="Amount of invoices to download.")
    args = parser.parse_args()

    browser = webdriver.Chrome()

    download_invoices_with_tracking_ids_as_pdf(args.invoices_amount)
