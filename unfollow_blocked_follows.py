#!/usr/bin/env python3

"""
unfollow_blocked_follows.py

Unfollows accounts that are both followed and blocked on BlueSky.
Outputs cursed follows to 'unfollow_blocked_follows_list.txt' and supports dry-run mode.

Usage:
    python unfollow_blocked_follows.py [--dryrun]

Arguments:
    --dryrun : Run in dry-run mode (no unfollows, just print actions).

Dependencies:
    - atproto: Python client for interacting with the BlueSky API.
    - configparser: For reading credentials from 'bluesky-config.ini'.
"""

import atproto
import sys
import os
import configparser
from typing import List, Set

# Configuration file for storing credentials
CONFIG_FILE = "bluesky-config.ini"

def load_config():
    """Load Bluesky handle and app password from 'bluesky-config.ini'."""
    config = configparser.ConfigParser()
    
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Config file '{CONFIG_FILE}' not found.")
        exit(1)

    config.read(CONFIG_FILE)

    try:
        handle = config["credentials"]["handle"]
        app_password = config["credentials"]["app_password"]
        return handle, app_password
    except KeyError as e:
        print(f"Error: Missing {e} in config file.")
        exit(1)

def create_files_if_not_exist():
    """Create external files if they don't exist."""
    files_to_create = ["unfollow_blocked_follows_list.txt"]
    for file in files_to_create:
        if not os.path.exists(file):
            print(f"Creating '{file}' as it does not exist.")
            open(file, "w").close()  # Create an empty file

def collect_blocks(bclient) -> Set:
    """
    Collect all blocked accounts' DIDs (Decentralized Identifiers).
    This function paginates through the results to gather all blocks.
    
    Returns:
        A set of DIDs of accounts that are blocked by the user.
    """
    blocks = set()
    cursor = None
    while True:
        # If no cursor, fetch the first page of blocks
        if not cursor:
            resp = bclient.app.bsky.graph.get_blocks()
        else:
            resp = bclient.app.bsky.graph.get_blocks({"cursor": cursor})

        # Add blocked accounts' DIDs to the set
        blocks.update(pv.did for pv in resp.blocks)

        # Check for pagination and continue fetching if needed
        if resp.cursor == cursor:
            break
        elif resp.cursor is None:
            break
        else:
            cursor = resp.cursor
    return blocks

def collect_records(bclient, did, collection) -> List:
    """
    Collect all records for the given DID and collection type (e.g., follows).
    
    Args:
        bclient: The BlueSky client used for API requests.
        did: The DID (Decentralized Identifier) of the user.
        collection: The type of collection to fetch (e.g., "app.bsky.graph.follow").
    
    Returns:
        A list of records (e.g., follows) for the given DID and collection.
    """
    records = []
    cursor = None
    while True:
        # If no cursor, fetch the first page of records
        if not cursor:
            resp = bclient.com.atproto.repo.list_records(
                {"repo": did, "collection": collection}
            )
        else:
            resp = bclient.com.atproto.repo.list_records(
                {"repo": did, "collection": collection, "cursor": cursor}
            )
        
        # Extend the list with the fetched records
        records.extend(resp.records)

        # Check for pagination and continue fetching if needed
        if resp.cursor == cursor:
            break
        elif resp.cursor is None:
            break
        else:
            cursor = resp.cursor
    return records

def main(dryrun):
    """
    Main function to log in to BlueSky, identify cursed follows (follows of blocked accounts),
    and unfollow them if not in dry-run mode.
    
    Args:
        dryrun: A flag indicating whether to simulate the unfollow action without making changes.
    """
    # Load credentials from the config file
    actor, apppassword = load_config()

    print(f"Logging in as actor: {actor}")
    bclient = atproto.Client()  # Initialize BlueSky client
    bclient.login(actor, apppassword)  # Log in with provided credentials

    # Collect blocked accounts' DIDs
    blocks = collect_blocks(bclient)

    # Collect records of followed accounts
    r_follows_raw = collect_records(bclient, actor, "app.bsky.graph.follow")
    r_follows = {rec.value.subject for rec in r_follows_raw}  # Set of followed accounts' DIDs

    # Find accounts that are both followed and blocked (the "cursed follows")
    cursed_follows = r_follows & blocks
    if cursed_follows:
        r_follows_dict = {rec.value.subject: rec for rec in r_follows_raw}  # Dictionary of follows by DID
        # Save cursed follows to file
        create_files_if_not_exist()  # Ensure the output file exists
        with open("unfollow_blocked_follows_list.txt", "w") as f:
            for c_follow in cursed_follows:
                f.write(f"{c_follow}\n")
        print(f"Saved {len(cursed_follows)} cursed follows to 'unfollow_blocked_follows_list.txt'.")

        for c_follow in cursed_follows:
            print(f"Cursed follow: {c_follow}")  # Print out cursed follow
            record = r_follows_dict[c_follow]  # Find the record for the cursed follow
            rkey = record.uri.split("/")[-1]  # Extract the record key from the URI
            if not dryrun:  # If not in dry-run mode, unfollow the account
                print(f"Unfollowing {c_follow}")
                bclient.com.atproto.repo.delete_record(
                    {"repo": actor, "collection": "app.bsky.graph.follow", "rkey": rkey}
                )
            else:
                # In dry-run mode, just simulate the action and print what would happen
                print(f"Dry-run: would unfollow {c_follow}")
    else:
        print("No cursed follows found.")  # No cursed follows to unfollow

if __name__ == "__main__":
    try:
        # Check if --dryrun flag is passed in command-line arguments
        dryrun_flag = "--dryrun" in sys.argv
        if dryrun_flag:
            sys.argv.remove("--dryrun")

        main(dryrun_flag)

    except IndexError:
        raise SystemExit("Usage: [python] unfollow_blocked_follows.py --dryrun")
