#!/bin/bash

echo "Starting to download your invoices."
invoices_amount=${1:-0}
./venv/bin/python download_invoices.py --invoices_amount=$invoices_amount
