---
name: firestore-bid-reader
description: Automatically reads new construction bids from the Firestore database to process outreach or compliance.
author: Ridis Enterprise
version: 1.0.0
---

# Instructions
When the user asks to "check for new bids" or when a scheduled cron job triggers:

1. Execute the local python script: `python3 read_bids.py`.
2. Parse the resulting JSON list of bids.
3. For each bid found:
    - Summarize the project details (Client, Amount, Location).
    - Change the status in Firestore to `processing` (using the update_bid tool if available).
    - Proceed to the next step in the "Outreach" workflow.

# Constraints
- Never output raw JSON to the user.
- If no bids are found, simply report "No new bids in the queue."
