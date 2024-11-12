#!/usr/bin/env python3
import argparse
import json
from src import process_file

def parse_args():
    parser = argparse.ArgumentParser(description='Load CSV data into PostgreSQL database')
    parser.add_argument('file_path', help='Path to the CSV file to import')
    parser.add_argument('table_name', help='Name of the target database table')
    parser.add_argument('--config', '-c', default='db_config.json',
                       help='Path to database configuration JSON file (default: db_config.json)')
    return parser.parse_args()

def load_db_config(config_path):
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file not found: {config_path}")
        print("Please create a JSON file with the following structure:")
        print("""
{
    "dbname": "your_database",
    "user": "your_username",
    "password": "your_password",
    "host": "your_host",
    "port": "5432"
}
        """)
        exit(1)
    except json.JSONDecodeError:
        print(f"Invalid JSON in configuration file: {config_path}")
        exit(1)

def main():
    args = parse_args()
    db_params = load_db_config(args.config)
    process_file(args.file_path, db_params, args.table_name)

if __name__ == '__main__':
    main()
