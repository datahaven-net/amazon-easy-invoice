# amazon-easy-invoice

Amazon invoice downloader as HTML with tracking id which belongs to that invoice.


## Installation

Clone project files locally.

Execute install.sh script to create virtual environment and install needed packages.

        $ ./install.sh
        
Download ChromeDriver. Note that, chromedriver version should be compatible with your Google Chrome in your local machine.

    https://chromedriver.chromium.org/downloads

Copy config_example.py as config.py and update your username, password and waiting times between pages (and if needed update urls).


## Download invoices
Execute the invoices.sh script

    $ ./invoices.sh

If you want to download specific amount of orders, you can give amount of invoices as below.

    $ ./invoices.sh 5

Script will create Downloads folder in the project. 
You can open html files which were downloaded in this folder.


## Troubleshooting

#### WebDriverException: Message: 'chromedriver' executable needs to be available in the path.

    $ export PATH="$PATH:/projects_folder"
