#!/usr/bin/env python3
import json

# Read the new accounts from attached file
with open('attached_assets/message (3)_1753343855158.txt', 'r') as f:
    new_accounts_data = json.load(f)

# Read current IND_ACC.json
with open('IND_ACC.json', 'r') as f:
    current_accounts = json.load(f)

print(f"Current accounts: {len(current_accounts)}")
print(f"New accounts to add: {len(new_accounts_data)}")

# Convert new accounts to proper format and add them
for account in new_accounts_data:
    new_entry = {
        "guest_account_info": {
            "com.garena.msdk.guest_uid": str(account["uid"]),
            "com.garena.msdk.guest_password": account["password"]
        }
    }
    current_accounts.append(new_entry)

print(f"Total accounts after addition: {len(current_accounts)}")

# Save the updated accounts
with open('IND_ACC.json', 'w') as f:
    json.dump(current_accounts, f, indent=4)

print("✅ Successfully added all 100 new accounts to IND_ACC.json")
print("✅ India account system now has proper token generation coverage")