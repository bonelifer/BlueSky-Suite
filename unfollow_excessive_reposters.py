#!/usr/bin/env python3

"""
unfollow_excessive_reposters.py

Unfollows accounts with excessive repost ratios on BlueSky. 
Supports dry-run mode and ignores handles listed in 'unfollow_excessive_reposters_list_ignore-list.txt'.
Outputs reposters to 'unfollow_excessive_reposters_list.txt'.

Usage:
    python unfollow_excessive_reposters.py [--dry] [--prod] [--repost RATIO] [--show-ignore]

Arguments:
    --dry         : Run in dry mode (no unfollows, just print actions).
    --prod        : Run in production mode (actually unfollow users).
    --repost      : Ratio of reposts to consider a user a reposter (default: 0.8).
    --show-ignore : Show ignored entries in the output.

Dependencies:
    - atproto: Python client for interacting with the BlueSky API.
    - configparser: For reading credentials from 'bluesky-config.ini'.
"""

import configparser
from atproto import Client
import argparse
import os

# Configuration and file paths
CONFIG_FILE = "bluesky-config.ini"  # File containing Bluesky credentials
IGNORE_LIST_FILE = "unfollow_excessive_reposters_list_ignore-list.txt"  # File containing handles to ignore
OUTPUT_FILE = "unfollow_excessive_reposters_list.txt"  # File to save reposters

# Domains to automatically ignore
IGNORE_DOMAINS = [
    "altgov.info",  # Example domain
    # Add more domains here as needed
]

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
    files_to_create = [IGNORE_LIST_FILE, OUTPUT_FILE]
    for file in files_to_create:
        if not os.path.exists(file):
            print(f"Creating '{file}' as it does not exist.")
            open(file, "w").close()  # Create an empty file

def load_ignore_list():
    """Load handles to ignore from 'unfollow_excessive_reposters_list_ignore-list.txt'."""
    create_files_if_not_exist()  # Ensure files exist
    ignore_list = []
    with open(IGNORE_LIST_FILE, "r") as file:
        for line in file:
            handle = line.strip()
            if handle and not handle.startswith("#"):
                ignore_list.append(handle)
    return ignore_list

def add_to_ignore_list(handle):
    """Add a handle to 'unfollow_excessive_reposters_list_ignore-list.txt' if it's not already present."""
    ignore_list = load_ignore_list()
    if handle not in ignore_list:
        with open(IGNORE_LIST_FILE, "a") as file:
            file.write(f"{handle}\n")
        print(f"Added {handle} to {IGNORE_LIST_FILE}.")

# Initialize the ATProto client with credentials from config file
handle, password = load_config()
client = Client()
client.login(handle, password)

# Load the ignore list
ignore_list = load_ignore_list()

def get_follows():
    """Fetch the list of people you are currently following."""
    follows = []
    limit = 100  # Number of follows to fetch per request
    response = client.get_follows(handle, None, limit)
    follows.extend(response.follows)
    return follows

def is_reposter(user, ratio=0.8):
    """Check if a user is a reposter based on their repost ratio."""
    response = client.get_author_feed(user.handle)
    if not response.feed:
        return False  # No posts, not a reposter

    # Count reposts in the user's feed
    reposts = sum(1 for post in response.feed if post.post.author.handle != user.handle)
    actual_ratio = reposts / len(response.feed)
    return actual_ratio > ratio

def unfollow(user):
    """Unfollow a user."""
    try:
        client.delete_follow(user.did)
        print(f"Unfollowed https://bsky.app/profile/{user.handle}")
    except Exception as e:
        print(f"Failed to unfollow https://bsky.app/profile/{user.handle}: {e}")

def action_on_users(follows, repost, dry=True, show_ignore=False):
    """Identify and take action on reposters, excluding ignored accounts."""
    reposter_count = 0

    for user in follows:
        # Automatically ignore and add handles containing domains from IGNORE_DOMAINS
        ignore_user = any(domain in user.handle for domain in IGNORE_DOMAINS)
        if ignore_user:
            add_to_ignore_list(user.handle)
            if show_ignore:
                print(f"Ignoring https://bsky.app/profile/{user.handle} (contains a domain in IGNORE_DOMAINS).")
            continue

        # Skip manually ignored accounts
        if user.handle in ignore_list:
            if show_ignore:
                print(f"Ignoring https://bsky.app/profile/{user.handle} (in ignore list).")
            continue

        # Check if the user is a reposter
        if is_reposter(user, repost):
            reposter_count += 1
            print(f"User https://bsky.app/profile/{user.handle} is a reposter.")
            # Save handle to output file
            with open(OUTPUT_FILE, "a") as f:
                f.write(f"{user.handle}\n")
            # Unfollow the user if not in dry mode
            if not dry:
                unfollow(user)

    # Print summary of actions
    if dry:
        print(f"Would unfollow {reposter_count} reposters. See {OUTPUT_FILE} for details.")
    else:
        print(f"Unfollowed {reposter_count} reposters. See {OUTPUT_FILE} for details.")

def main(dry=False, prod=False, repost=0.8, show_ignore=False):
    """Main function to execute the script."""
    follows = get_follows()
    action_on_users(follows, repost, not prod, show_ignore)

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Unfollow reposters on Bluesky.")
    parser.add_argument('--dry', action='store_true', help="Run without actually unfollowing users.")
    parser.add_argument('--prod', action='store_true', help="Run in production mode and actually unfollow users.")
    parser.add_argument('--repost', type=float, default=0.8, help="Ratio of reposts before unfollowing.")
    parser.add_argument('--show-ignore', action='store_true', help="Show ignored entries in the output.")

    args = parser.parse_args()
    main(args.dry, args.prod, args.repost, args.show_ignore)
