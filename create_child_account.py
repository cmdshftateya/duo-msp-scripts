import os
import sys
import duo_client

def get_api_credentials() -> dict:
    """Retrieve API credentials from environment variables."""
    required_vars = ["DUO_ACCOUNTS_IKEY", "DUO_ACCOUNTS_SKEY", "DUO_ACCOUNTS_HOST"]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    return {
        "IKEY": os.getenv("DUO_ACCOUNTS_IKEY="),
        "SKEY": os.getenv("DUO_ACCOUNTS_SKEY="),
        "APIHOST": os.getenv("DUO_ACCOUNTS_HOST="),
    }

def create_child_account(account_client, account_name):
    """Create a Duo child account with the given name."""
    print(f"Creating child account with name [{account_name}]")
    child_account = account_client.create_account(account_name)

    if 'account_id' in child_account:
        print(f"Child account for [{account_name}] created successfully.")
    else:
        print(f"An unexpected error occurred while creating child account for {account_name}")
    
    print(child_account)

def main():
    """Main program entry point"""
    credentials = get_api_credentials()
    account_client = duo_client.Accounts(
        ikey=credentials["IKEY"],
        skey=credentials["SKEY"],
        host=credentials["APIHOST"]
    )

    if len(sys.argv) > 1:
        # Batch mode: Loop through provided arguments and create accounts
        for account_name in sys.argv[1:]:
            create_child_account(account_client, account_name)
    else:
        # Interactive mode: Prompt user for an account name
        account_name = input("Enter account name to create: ").strip()
        if account_name:
            create_child_account(account_client, account_name)
        else:
            print("No account name provided. Exiting.")

if __name__ == '__main__':
    main()