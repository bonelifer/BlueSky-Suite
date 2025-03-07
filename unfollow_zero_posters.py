#!/usr/bin/env python3

"""
unfollow_zero_posters.py

Unfollows accounts with zero posts on BlueSky. 
Supports ignore lists and always-unfollow lists. 
Generates 'unfollow_zero_posters_list.txt' for review before unfollowing.

Usage:
    python unfollow_zero_posters.py --dump [--strict]
    python unfollow_zero_posters.py --remove

Arguments:
    --dump   : Dump users with zero posts to 'unfollow_zero_posters_list.txt'.
    --remove : Unfollow users listed in 'unfollow_zero_posters_list.txt'.
    --strict : Exclude replies and reposts when checking for posts.

Dependencies:
    - atproto: Python client for interacting with the BlueSky API.
    - configparser: For reading credentials from 'bluesky-config.ini'.
"""

from datetime import timezone
from atproto import Client
import datetime
import configparser
import os

# Load credentials from the configuration file
config = configparser.ConfigParser()
config.read('bluesky-config.ini')

# Fetch user credentials from the configuration file
handle = config.get('credentials', 'handle')
password = config.get('credentials', 'app_password')

# Initialize the BlueSky API client
client = Client()

# Attempt login using credentials from the config file
try:
    client.login(handle, password)
    print("Login successful.")
except Exception as e:
    print(f"Login failed: {e}")
    exit(1)

def get_follows():
    """Fetch the list of accounts the user is following."""
    follows = []
    response = client.get_follows(handle, None, 100)
    follows.extend(response.follows)

    # Paginate through the results if more follows exist
    while response.cursor:
        response = client.get_follows(handle, response.cursor, 100)
        follows.extend(response.follows)

    return follows

def is_zero_post(user, strict=False):
    """Check if a user has zero posts. If `strict` is True, only original posts (not replies or reposts) are counted."""
    try:
        response = client.get_author_feed(user.handle)

        if not response.feed:
            return True  # Return True if no posts are found

        if strict:
            # Filter posts to only include original posts, excluding replies and reposts
            original_posts = [
                post for post in response.feed
                if not hasattr(post.post.record, "reply")  # Exclude replies
                and not hasattr(post.post.record, "embed")  # Exclude reposts
            ]
            return len(original_posts) == 0  # Return True if no original posts exist

        return False  # Return False if user has posts, even if they are replies/reposts
    except Exception as e:
        print(f"Error checking posts for {user.handle}: {e}")
        return False  # Assume user has posts if there is an error

def create_files_if_not_exist():
    """Create external files if they don't exist during the dump operation."""
    files_to_create = [
        "unfollow_zero_posters_list.txt",
        "unfollow_zero_posters_ignore_list.txt",
        "always_unfollow_list.txt"
    ]
    for file in files_to_create:
        if not os.path.exists(file):
            print(f"Creating '{file}' as it does not exist.")
            open(file, "w").close()  # Create an empty file

def dump_users_with_zero_posts(follows, ignore_list, strict=False):
    """Dump users with zero posts to 'unfollow_zero_posters_list.txt' for manual review before unfollowing."""
    create_files_if_not_exist()  # Create files if they don't exist
    with open("unfollow_zero_posters_list.txt", "w") as f:
        for user in follows:
            if user.handle in ignore_list:
                print(f"Skipping {user.handle}: In ignore list.")
                continue
            if is_zero_post(user, strict):
                f.write(f"{user.handle}\n")
    print("Dumped users with zero posts to 'unfollow_zero_posters_list.txt'.")
    print("Review the file before running '--remove' to unfollow users.")

def unfollow_users_from_file(ignore_list, always_unfollow_list):
    """Unfollow users listed in 'unfollow_zero_posters_list.txt', respecting ignore and always unfollow lists."""
    if not os.path.exists("unfollow_zero_posters_list.txt"):
        print("Error: 'unfollow_zero_posters_list.txt' not found.")
        print("Run `python unfollow_zero_posters.py --dump` first.")
        exit(1)

    # Load users to unfollow from 'unfollow_zero_posters_list.txt'
    with open("unfollow_zero_posters_list.txt", "r") as f:
        users_to_unfollow = [line.strip() for line in f if line.strip()]

    if not users_to_unfollow:
        print("No users to unfollow. 'unfollow_zero_posters_list.txt' is empty.")
        return

    unfollow_count = 0  # Initialize the counter for unfollowed users

    # First, unfollow users in the 'always_unfollow_list', no matter their post count
    for user_handle in always_unfollow_list:
        try:
            user = client.get_profile(user_handle)
            if user.viewer and user.viewer.following:
                client.delete_follow(user.viewer.following)
                unfollow_count += 1
                print(f"Unfollowed {user_handle} (from always unfollow list)")
            else:
                print(f"Skipping {user_handle}: Not currently following")
        except Exception as e:
            print(f"Failed to unfollow {user_handle} (always unfollow): {e}")

    # Then, unfollow users from 'unfollow_zero_posters_list.txt', skipping the ones in the ignore list
    for user_handle in users_to_unfollow:
        if user_handle in ignore_list:
            print(f"Skipping {user_handle}: In ignore list.")
            continue

        try:
            user = client.get_profile(user_handle)
            if user.viewer and user.viewer.following:
                client.delete_follow(user.viewer.following)
                unfollow_count += 1
                print(f"Unfollowed {user_handle}")
            else:
                print(f"Skipping {user_handle}: Not currently following")
        except Exception as e:
            print(f"Failed to unfollow {user_handle}: {e}")

    print(f"Unfollowed {unfollow_count} users.")

def load_ignore_list(ignore_file="unfollow_zero_posters_ignore_list.txt"):
    """Load the list of users to ignore from 'unfollow_zero_posters_ignore_list.txt'."""
    ignore_list = []
    if os.path.exists(ignore_file):
        with open(ignore_file, "r") as f:
            ignore_list = [line.strip() for line in f if line.strip()]
    return ignore_list

def load_always_unfollow_list():
    """Load the list of users to always unfollow from 'always_unfollow_list.txt'."""
    always_unfollow_list = []
    if os.path.exists("always_unfollow_list.txt"):
        with open("always_unfollow_list.txt", "r") as f:
            always_unfollow_list = [line.strip() for line in f if line.strip()]
    return always_unfollow_list

def main(dump=False, remove=False, strict=False, ignore_file="unfollow_zero_posters_ignore_list.txt"):
    """Run the script in either dump mode (to identify zero posters) or remove mode (to unfollow users)."""
    ignore_list = load_ignore_list(ignore_file)
    always_unfollow_list = load_always_unfollow_list()

    if dump:
        follows = get_follows()
        dump_users_with_zero_posts(follows, ignore_list, strict)
    elif remove:
        unfollow_users_from_file(ignore_list, always_unfollow_list)
    else:
        print("Error: You must specify either `--dump` or `--remove`.")
        exit(1)

if __name__ == "__main__":
    import argparse

    # Set up argument parser for command-line options
    parser = argparse.ArgumentParser(description="Unfollow users with zero posts.")
    parser.add_argument('--dump', action='store_true', help="Dump users to a file for review. **Must be run before --remove**.")
    parser.add_argument('--remove', action='store_true', help="Unfollow users from the file. **Requires 'unfollow_zero_posters_list.txt'.**")
    parser.add_argument('--strict', action='store_true', help="Exclude replies and reposts when checking for posts.")

    # Parse command-line arguments
    args = parser.parse_args()
    main(dump=args.dump, remove=args.remove, strict=args.strict)
