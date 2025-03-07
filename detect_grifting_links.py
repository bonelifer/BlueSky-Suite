#!/usr/bin/env python3

"""
detect_grifting_links.py

Detects accounts sharing grifting links (e.g., donation links) on BlueSky. 
Saves handles to 'detect_grifting_links_handles.txt' and ignores handles listed in 'detect_grifting_links_ignore_handles.txt'.

Usage:
    python detect_grifting_links.py

Dependencies:
    - atproto: Python client for interacting with the BlueSky API.
    - urlextract: For extracting URLs from posts.
    - configparser: For reading credentials from 'bluesky-config.ini'.
"""

import os
import configparser
from atproto import Client
from urlextract import URLExtract

# Configuration and file paths
CONFIG_FILE = "bluesky-config.ini"  # File containing Bluesky credentials
IGNORE_HANDLES_FILE = "detect_grifting_links_ignore_handles.txt"  # File containing handles to ignore
OUTPUT_FILE = "detect_grifting_links_handles.txt"  # File to save handles with grifting links

# List of keywords to check for grifting links
GRIFTING_KEYWORDS = ['gofund', 'paypal', 'gaza', 'palestinian', 'God fearing', 'ko.fi']

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
    files_to_create = [IGNORE_HANDLES_FILE, OUTPUT_FILE]
    for file in files_to_create:
        if not os.path.exists(file):
            print(f"Creating '{file}' as it does not exist.")
            open(file, "w").close()  # Create an empty file

def load_ignore_handles():
    """Load handles to ignore from 'detect_grifting_links_ignore_handles.txt'."""
    create_files_if_not_exist()  # Ensure files exist
    ignore_handles = set()
    with open(IGNORE_HANDLES_FILE, "r") as file:
        for line in file:
            handle = line.strip()
            if handle:
                ignore_handles.add(handle)
    return ignore_handles

# Initialize the ATProto client with credentials from config file
handle, password = load_config()
client = Client()
user = client.login(handle, password)

extractor = URLExtract()
ignore_handles = load_ignore_handles()

def check_for_grifting_links(feed):
    """Check if any post in the feed contains grifting links."""
    for item in feed:
        for link in extractor.find_urls(item.post.record.text):
            if any(keyword in link for keyword in GRIFTING_KEYWORDS):
                return True
    return False

# Open the output file in append mode
with open(OUTPUT_FILE, "w") as output_file:
    # Check followers
    data = client.get_followers(actor=user.did, limit=100)
    while data:
        for follower in data.followers:
            if follower.handle in ignore_handles:
                continue  # Skip ignored handles
            feed_data = client.get_author_feed(actor=follower.did, filter='posts_and_author_threads', limit=100)
            if check_for_grifting_links(feed_data.feed):
                # Print to terminal (unchanged)
                print(f'https://bsky.app/profile/{follower.handle}')
                # Save handle to file
                output_file.write(f"{follower.handle}\n")

        if data.cursor:
            data = client.get_followers(actor=user.did, limit=100, cursor=data.cursor)
        else:
            data = None

    # Check follows
    data = client.get_follows(actor=user.did, limit=100)
    while data:
        for follow in data.follows:
            if follow.handle in ignore_handles:
                continue  # Skip ignored handles
            feed_data = client.get_author_feed(actor=follow.did, filter='posts_and_author_threads', limit=100)
            if check_for_grifting_links(feed_data.feed):
                # Print to terminal (unchanged)
                print(f'https://bsky.app/profile/{follow.handle}')
                # Save handle to file
                output_file.write(f"{follow.handle}\n")

        if data.cursor:
            data = client.get_follows(actor=user.did, limit=100, cursor=data.cursor)
        else:
            data = None
