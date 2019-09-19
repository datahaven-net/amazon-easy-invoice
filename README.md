# amazon-easy-invoice

Amazon invoice downloader as HTML with tracking id which belongs to that invoice.


## Installation

Clone project files locally.
Create a virtual environment. Note that, this project only supports Python3.6 and above.

        $ virtualenv -p python3 venv

Activate your virtual environment.

        $ source venv/bin/activate

Install the requirements.

        $ pip install -r requirements.txt
        
Download ChromeDriver. Note that, chromedriver version should be compatible with your Google Chrome in your local machine.

    https://chromedriver.chromium.org/downloads

Copy config_example.py as config.py and update your username and password (and if needed update urls).


## Download invoices
Run the script

    $ python download_invoices.py

Script will create Downloads folder in the project. 
You can open html files which were downloaded in this folder. 
