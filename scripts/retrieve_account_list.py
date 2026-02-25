import os
import sys
import duo_client
from pprint import pprint
from tabulate import tabulate

def get_api_credentials() -> dict:
    """Retrieve API credentials from environment variables."""
    credentials = {
        "IKEY": os.getenv("DUO_ACCOUNTS_IKEY"),
        "SKEY": os.getenv("DUO_ACCOUNTS_SKEY"),
        "APIHOST": os.getenv("DUO_ACCOUNTS_HOST")
    }
    
    # Raise an error if any of the credentials are missing
    if not credentials["IKEY"] or not credentials["SKEY"] or not credentials["APIHOST"]:
        raise ValueError("Missing required environment variables: DUO_ACCOUNTS_IKEY, DUO_ACCOUNTS_SKEY, or DUO_ACCOUNTS_HOST")
    
    return credentials

def main():
    """Main program entry point"""
    credentials = get_api_credentials()
    account_client = duo_client.Accounts(
        ikey=credentials['IKEY'],
        skey=credentials['SKEY'],
        host=credentials['APIHOST']
    )
    
    child_accounts = account_client.get_child_accounts()
    
    if isinstance(child_accounts, list):
        # Prepare data for tabulation
        table_data = []
        for child_account in child_accounts:
            table_data.append([child_account['account_id'], child_account['api_hostname'], child_account['name']])
        
        # Print data as a clean table
        headers = ["Account ID", "API Hostname", "Name"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
    elif isinstance(child_accounts, dict):
        # Non-successful response returned
        pprint(child_accounts)

if __name__ == '__main__':
    main()
