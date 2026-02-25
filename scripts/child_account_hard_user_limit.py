"""
Duo Security Child Account User Limit Manager

This script allows you to get or set the hard user limit for a Duo Security child account.
It uses the Accounts API from the parent account to manage child account settings.

Configuration:
    The script uses duo.conf file for API credentials. The file should contain:
    - DUO_ACCOUNTS_IKEY (Parent Account's Accounts API integration key)
    - DUO_ACCOUNTS_SKEY (Parent Account's Accounts API secret key)
    - DUO_ACCOUNTS_HOST (Parent Account's Accounts API hostname)

Required Information:
    Child Account Information:
    - Account ID (account_id) - starts with 'DA'
    - API Hostname (child_api_host)
    These can be found in the response from /accounts/v1/account/list

Usage:
    python3 child_account_hard_user_limit.py
    Then enter the following space-separated values in this exact order:
    1. Child Account ID (account_id)
    2. Child Account's API Hostname (child_api_host)
    3. [Optional] Desired Limit (number)

    If desired_limit is provided, it will set the limit.
    If desired_limit is omitted, it will get the current limit.

Example:
    # To get current limit:
    python3 child_account_hard_user_limit.py
    DXXXXXXXXXXXXXXXXXX api-XXXXXXXX.duosecurity.com

    # To set a new limit:
    python3 child_account_hard_user_limit.py
    DXXXXXXXXXXXXXXXXXX api-XXXXXXXX.duosecurity.com 100
"""

import duo_client
import configparser
import os

def load_config():
    """Load configuration from duo.conf file"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'duo.conf')
    
    if not os.path.exists(config_path):
        raise FileNotFoundError("duo.conf file not found. Please create it with your API credentials.")
    
    config.read(config_path)
    
    # Get Accounts API credentials
    ikey = config.get('DEFAULT', 'DUO_ACCOUNTS_IKEY', fallback=None)
    skey = config.get('DEFAULT', 'DUO_ACCOUNTS_SKEY', fallback=None)
    host = config.get('DEFAULT', 'DUO_ACCOUNTS_HOST', fallback=None)
    
    if not all([ikey, skey, host]):
        raise ValueError("Missing required credentials in duo.conf file")
    
    return ikey, skey, host

class CustomDuoAdmin(duo_client.admin.AccountAdmin):
    # Setter
    def set_user_limit(self, account_id, desired_hard_limit):
        """Method to call the hidden /admin/v1/billing/user_limit endpoint to set user limit"""
        endpoint = '/admin/v1/billing/user_limit'
        params = {
            'account_id': account_id,
            'user_limit': str(desired_hard_limit)  # Correct parameter name
        }
        response = self.json_api_call('POST', endpoint, params)
        return response
    
    # Getter
    def get_user_limit(self, account_id):
        """Method to call the hidden /admin/v1/billing/user_limit endpoint to get user limit"""
        endpoint = '/admin/v1/billing/user_limit'
        params = {
            'account_id': account_id,
        }
        response = self.json_api_call('GET', endpoint, params)
        return response


def validate_account_id(account_id):
    """Validate account ID format"""
    if not account_id.startswith('DA'):
        raise ValueError("Account ID must start with 'DA'")
    return account_id

def prompt_for_credentials():
    """Prompt user for all required inputs"""
    print("\nPlease enter the following space-separated values in this exact order:")
    print("1. Child Account ID (account_id) - starts with 'DA'")
    print("2. Child Account's API Hostname (child_api_host)")
    print("3. [Optional] Desired Limit (number)")
    print("\nExample:")
    print("# To get current limit:")
    print("DXXXXXXXXXXXXXXXXXX api-XXXXXXXX.duosecurity.com")
    print("\n# To set a new limit:")
    print("DXXXXXXXXXXXXXXXXXX api-XXXXXXXX.duosecurity.com 100")
    print("\nEnter values:")
    
    user_input = input().strip()
    inputs = user_input.split()

    if len(inputs) < 2:
        raise ValueError("Insufficient arguments provided. Expected at least 2 arguments.")

    try:
        account_id = validate_account_id(inputs[0])
        child_api_host = inputs[1]
        desired_limit = int(inputs[2]) if len(inputs) > 2 else None

        if desired_limit is not None and desired_limit < 0:
            raise ValueError("Invalid limit. Please select a value 0 or higher")

        return account_id, child_api_host, desired_limit
    except ValueError as e:
        raise ValueError(f"Input validation error: {str(e)}")
    except IndexError:
        raise ValueError("Incorrect number of arguments provided")


def main():
    """Main program entry point"""
    try:
        # Load configuration from duo.conf
        parent_ikey, parent_skey, parent_host = load_config()
        
        # Get child account information from user
        account_id, child_api_host, desired_limit = prompt_for_credentials()
        
        print("\nUsing the following configuration:")
        print(f"Child Account ID: {account_id}")
        print(f"Child Account Host: {child_api_host}")
        if desired_limit is not None:
            print(f"Setting limit to: {desired_limit}")
        else:
            print("Getting current limit")
        
        # Initialize the custom admin class with the parent account credentials
        account_admin_api = CustomDuoAdmin(
            ikey=parent_ikey,
            skey=parent_skey,
            host=child_api_host,  # Use child account's host for the actual request
            account_id=account_id
        )

        if desired_limit is not None:
            print(f"\nSetting hard user limit for account ID {account_id} to {desired_limit}")
            result = account_admin_api.set_user_limit(account_id, str(desired_limit))
        else:
            print(f"\nGetting hard user limit for account ID {account_id}")
            result = account_admin_api.get_user_limit(account_id)

        print("\nResult:")
        print(result)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("\nPlease verify:")
        print("1. The duo.conf file exists and contains valid credentials")
        print("2. The child account ID and hostname are correct")
        print("3. The parent account has permission to manage the child account")
        print("4. The input values are in the correct order")


if __name__ == '__main__':
    main()