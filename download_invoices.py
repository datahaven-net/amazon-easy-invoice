import argparse
import os
import re
from urllib import parse as urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config


class AmazonEasyInvoice(object):
    def __init__(self, amount_of_invoices):
        self.amount_of_invoices = amount_of_invoices
        self.browser = webdriver.Chrome()

    def __call__(self):
        self.login()
        self.download_invoices_with_tracking_ids_as_pdf(self.amount_of_invoices)

    def login(self):
        self.browser.get(config.AMAZON_LOGIN_URL)

        # Fill username
        try:
            email = self.browser.find_element_by_name("email")
            WebDriverWait(self.browser, config.WAITING_TIME_BETWEEN_PAGES)
        except TimeoutException:
            raise Exception("Email filling page could not be loaded.")

        email.send_keys(config.AMAZON_USER_EMAIL)
        email.submit()

        # Fill password
        try:
            password = self.browser.find_element_by_name("password")
            WebDriverWait(self.browser, config.WAITING_TIME_BETWEEN_PAGES)
        except TimeoutException:
            raise Exception("Password page could not be loaded.")
        password.send_keys(config.AMAZON_USER_PASSWORD)

        # Click "remember me" check box.
        self.browser.find_element_by_xpath(
            ".//*[contains(text(), 'Keep me signed in')]"
        ).click()

        password.submit()

        try:
            WebDriverWait(self.browser, config.WAITING_TIME_AFTER_LOGIN).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[contains(@href, 'order-history')]")
                )
            )
        except TimeoutException:
            print(f'You could not login in {config.WAITING_TIME_AFTER_LOGIN} seconds')
            self.browser.quit()

    def get_tracking_id(self):
        """

        :return: tracking_id
        """

        try:
            tracking_id = self.browser.find_element_by_partial_link_text("Tracking").text.split(" ")[-1]
        except Exception:
            tracking_id = ""

        if not tracking_id:
            try:
                tracking_id = self.browser.find_elements_by_xpath("//*[contains(text(), 'Tracking ID')]")[0].text.split()[-1]
            except Exception:
                tracking_id = ""

        return tracking_id

    def get_delivery_company(self):
        """

        :return: delivery_by: name of the delivery company
        """

        try:
            # Amazon.com shows delivery company with "Shipped with" sentence.
            delivery_by = self.browser.find_elements_by_xpath("//*[contains(text(), 'Shipped with')]")[0].text
        except Exception:
            delivery_by = ""

        if not delivery_by:
            try:
                # Some other amazon websites like amazon.de shows delivery company with "Delivery By" sentence.
                delivery_by = self.browser.find_elements_by_xpath("//*[contains(text(), 'Delivery By')]")[0].text
            except Exception:
                delivery_by = ""

        return delivery_by

    def wait_progress_tracker_page_to_be_loaded(self):
        try:
            WebDriverWait(self.browser, config.WAITING_TIME_BETWEEN_PAGES).until(
                EC.presence_of_element_located(
                    (By.PARTIAL_LINK_TEXT, "Tracking ID")
                )
            )
        except TimeoutException:
            pass

    def get_ordered_item_names(self):
        """

        :return: item_names: all items which are belong to same progress tracker
        """
        length_of_items = len(self.browser.find_elements_by_xpath("//a[contains(@href, 'gp/product')]"))
        item_names = []
        for i in range(length_of_items):
            item_url = self.browser.find_elements_by_xpath("//a[contains(@href, 'gp/product')]")[i]
            item_url.click()
            try:
                wait = WebDriverWait(self.browser, config.WAITING_TIME_BETWEEN_PAGES)
                wait.until(lambda driver: "gp/product" in self.browser.current_url)
            except TimeoutException:
                raise Exception(f"Product page could not be loaded.")

            item_names.append(self.browser.title)
            self.browser.back()
            self.wait_progress_tracker_page_to_be_loaded()

        return item_names

    def get_all_orders_with_tracking_info(self, amount_of_invoices):
        """
        :param amount_of_invoices: Amount of the invoices to gather the info about
        :return: orders: all orders as list of order ids which have the list of tracking information with tracking_id,
        name of the delivery company and ordered items which belong to that specific tracking_id.
        """

        self.browser.get(config.AMAZON_ORDERS_URL)

        try:
            wait = WebDriverWait(self.browser, config.WAITING_TIME_BETWEEN_PAGES)
            wait.until(lambda driver: "order-history" in self.browser.current_url)
        except TimeoutException:
            raise Exception(f"Order page could not be loaded.")

        order_urls = self.browser.find_elements_by_xpath("//a[contains(@href, 'progress-tracker')]")

        progress_tracker_urls = []
        for order_url in order_urls:
            progress_tracker_urls.append(order_url.get_attribute("href"))

        order_urls_length = len(order_urls)
        WebDriverWait(order_urls, config.WAITING_TIME_BETWEEN_PAGES)

        if not order_urls_length:
            print('You do not have any order at this moment.')
            self.browser.quit()

        print(f'Total track packages amount is {order_urls_length}')

        # Check if the given input to download invoices is equal or less than total orders. If not, download all orders.
        if 0 < amount_of_invoices <= order_urls_length:
            total_invoices_to_download = amount_of_invoices
        else:
            total_invoices_to_download = order_urls_length
        print(f'Total amount invoices to download is {total_invoices_to_download}')
        orders = []

        for i in range(total_invoices_to_download):
            # Go to the progress tracker of the order.
            print(f'Going to click track package link number {i+1}')
            self.browser.get(progress_tracker_urls[i])
            self.wait_progress_tracker_page_to_be_loaded()

            # Get the order id from the URL of the progress tracker
            current_url = self.browser.current_url
            parsed = urlparse.urlparse(current_url)
            order_id = urlparse.parse_qs(parsed.query)["orderId"][0]

            # Collect tracking id, delivery company and name of the items which are tracked in the progress tracker.
            tracked_item = {
                "tracking_id": self.get_tracking_id(),
                "delivery_by": self.get_delivery_company(),
                "item_names": self.get_ordered_item_names(),
            }

            # If order_id already exists, that means there are multiple tracking for the same order
            # with different items. So, extend same order_id with new tracked_item.
            # Else, add order_id with tracked_item as it's not existing yet.
            if any(order_id in order for order in orders):
                for order in orders:
                    if order_id in order:
                        index = orders.index(order)
                        orders[index][order_id].append(tracked_item)
            else:
                orders.append({order_id: [tracked_item]})

        return orders

    def download_invoices_with_tracking_ids_as_pdf(self, amount_of_invoices):
        """
        Downloads the invoices with order ids, tracking ids, delivery company name and
        ordered items belong to specific tracking id.
        """
        orders_with_tracking_info = self.get_all_orders_with_tracking_info(amount_of_invoices)

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

                self.browser.get(config.AMAZON_ORDER_INVOICE_URL + order_id)
                items_as_html = ', <br /> '.join(items)

                with open(html_file, 'wb') as f:
                    page_content = self.browser.page_source
                    page_content_encoded = page_content.replace(
                        re.findall(
                            f'{order_id}', page_content)[0], f"{order_id} <br /> "
                                                             f"<b>Tracking ID</b>: {tracking_id} <br /> "
                                                             f"<b>{delivery_by}</b> <br /> "
                                                             f"<b><u>ORDERED ITEMS:</b></u> <br /> {items_as_html}",
                    ).encode('utf-8')
                    f.write(page_content_encoded)
        print("You can find your invoices in Downloads folder in the project folder.")
        self.browser.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--invoices_amount", type=int, default=0, help="Amount of invoices to download.")
    args = parser.parse_args()

    AmazonEasyInvoice(args.invoices_amount)()
