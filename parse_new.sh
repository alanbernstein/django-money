#!/bin/bash
# after downloading a new statement and moving it to the appropriate directory,
# run these two statements to do all automated things that are currently implemented

pm parse_pdf_statements
pm manage_transactions -a alan-chase-credit --auto-add-merchants
