# BlueSky Management Scripts

A suite of Python scripts for managing your BlueSky account, including unfollowing inactive accounts, detecting grifting links, identifying suspended accounts, and more. These scripts use the `atproto` library to interact with the BlueSky API.

---

## Scripts

| Script Name                          | Description                                                                 |
|--------------------------------------|-----------------------------------------------------------------------------|
| `find_suspended_accounts.py`         | Finds and lists suspended or inactive accounts you follow.                   |
| `detect_grifting_links.py`           | Detects accounts sharing grifting links (e.g., donation links).              |
| `unfollow_zero_posters.py`           | Unfollows accounts with zero posts (optional: exclude replies and reposts).  |
| `unfollow_excessive_reposters.py`    | Unfollows accounts with excessive repost ratios.                             |
| `unfollow_blocked_follows.py`        | Unfollows accounts that are both followed and blocked.                       |

---

## Usage

### Prerequisites & Dependencies
- Python 3.x
- `atproto` library (`pip install atproto`)
- A BlueSky account and app password (stored in `bluesky-config.ini`).

All dependencies are listed in the `requirements.txt` file. To install them, run:

```bash
pip install -r requirements.txt
```

### Configuration
Rename `bluesky-config.ini.example` to `bluesky-config.ini` and update it with your BlueSky credentials:

```ini
[credentials]
handle = your_handle.bsky.social
app_password = your_app_password
```

**Note**: Replace `your_handle.bsky.social` with your BlueSky handle and `your_app_password` with your app password. The `bluesky-config.ini` file should not be shared or committed to version control.

### Running the Scripts
1. **Find Suspended Accounts**:
   ```bash
   python find_suspended_accounts.py --suspended --dump
   ```

2. **Detect Grifting Links**:
   ```bash
   python detect_grifting_links.py
   ```

3. **Unfollow Zero Posters**:
   ```bash
   python unfollow_zero_posters.py --dump  # Generate list
   python unfollow_zero_posters.py --remove  # Unfollow accounts
   ```

4. **Unfollow Excessive Reposters**:
   ```bash
   python unfollow_excessive_reposters.py --dry  # Simulate unfollows
   python unfollow_excessive_reposters.py --prod  # Actually unfollow
   ```

5. **Unfollow Blocked Follows**:
   ```bash
   python unfollow_blocked_follows.py --dryrun  # Simulate unfollows
   python unfollow_blocked_follows.py  # Actually unfollow
   ```

---

## License

This project is licensed under the **GNU General Public License v3.0**.
