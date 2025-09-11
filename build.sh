#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Create database tables if they don't exist
python setup_db_secure.py
