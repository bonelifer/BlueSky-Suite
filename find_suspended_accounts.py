#!/usr/bin/env python3

"""
find_suspended_accounts.py

Finds and manages suspended or inactive accounts on BlueSky. 
Outputs a list of suspended accounts to 'find_suspended_accounts_list.txt'.

Usage:
    python find_suspended_accounts.py --suspended [--dump]

Arguments:
    --suspended : Fetch suspended accounts from the list of followed accounts.
    --dump      : Save the list of suspended accounts to 'find_suspended_accounts_list.txt'.

Dependencies:
    - atproto: Python client for interacting with the BlueSky API.
    - configparser: For reading credentials from 'bluesky-config.ini'.
"""

import sys
import argparse
import configparser
from atproto import Client

# Define configuration file path
CONFIG_FILE = "bluesky-config.ini"

def load_config():
    """Load BlueSky credentials from the configuration file."""
    config = configparser.ConfigParser()
    if not config.read(CONFIG_FILE):
        print(f"Error: Configuration file '{CONFIG_FILE}' not found. Please create it.")
        sys.exit(1)

    try:
        handle = config["credentials"]["handle"]
        app_password = config["credentials"]["app_password"]
    except KeyError:
        print("Error: Invalid configuration file format. Ensure it contains 'handle' and 'app_password'.")
        sys.exit(1)

    return handle, app_password

def create_files_if_not_exist():
    """Create external files if they don't exist."""
    files_to_create = ["find_suspended_accounts_list.txt"]
    for file in files_to_create:
        if not os.path.exists(file):
            print(f"Creating '{file}' as it does not exist.")
            open(file, "w").close()  # Create an empty file

def fetch_suspended_accounts(client, actor_handle):
    """Fetch suspended accounts from the list of followed accounts."""
    try:
        follows = client.get_follows(actor_handle)  # Get the list of accounts the user is following
        suspended_accounts = []

        # Iterate over the follow list and check each account
        for follow in follows.follows:
            # Fetch account profile
            profile = client.get_profile(follow.handle)

            # Check if the account is suspended
            if hasattr(profile, "suspended") and profile.suspended:
                suspended_accounts.append({"handle": follow.handle, "did": follow.did})

        return suspended_accounts

    except Exception as e:
        print(f"Error fetching suspended accounts: {e}")
        sys.exit(1)

def dump_accounts(accounts, filename):
    """Dump account data to a file for inspection."""
    try:
        with open(filename, "w") as f:
            for account in accounts:
                f.write(f"{account['handle']}\n")
        print(f"Accounts dumped to {filename}.")
    except Exception as e:
        print(f"Error dumping accounts: {e}")

def main():
    """Main function to handle the CLI."""
    handle, app_password = load_config()

    # Initialize the BlueSky client
    client = Client()
    client.login(handle, app_password)

    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="Manage BlueSky accounts.")
    parser.add_argument("--suspended", action="store_true", help="Fetch suspended accounts.")
    parser.add_argument("--dump", action="store_true", help="Dump suspended accounts to a file.")
    args = parser.parse_args()

    if args.dump and not args.suspended:
        print("Error: --dump requires --suspended to be specified.")
        sys.exit(1)

    if args.suspended:
        # Fetch suspended accounts if --suspended is provided
        suspended_accounts = fetch_suspended_accounts(client, handle)
        if args.dump:
            # Dump accounts to file if --dump is provided
            create_files_if_not_exist()  # Ensure the output file exists
            dump_accounts(suspended_accounts, "find_suspended_accounts_list.txt")

if __name__ == "__main__":
    main()
