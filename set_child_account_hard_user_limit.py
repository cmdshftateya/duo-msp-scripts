import os
import duo_client
import argparse
import getpass

class CustomDuoAdmin(duo_client.admin.AccountAdmin):
    def set_user_limit(self, account_id, desired_hard_limit):
        """Method to call the hidden /admin/v1/billing/user_limit endpoint to set user limit"""
        endpoint = '/admin/v1/billing/user_limit'
        params = {
            'account_id': account_id,
            'user_limit': str(desired_hard_limit)  # Correct parameter name
        }
        response = self.json_api_call('POST', endpoint, params)
        return response


def check_environment_variables():
    """Check if the required environment variables are set and provide instructions if not"""
    ikey = os.getenv('DUO_IKEY')
    skey = os.getenv('DUO_SKEY')
    host = os.getenv('DUO_HOST')

    if not ikey or not skey or not host:
        print("Environment variables DUO_IKEY, DUO_SKEY, and DUO_HOST must be set.")
        print("To set up the environment variables, follow these steps:")
        print("1. Create a virtual environment: python -m venv env")
        print("2. Activate the virtual environment:")
        print("   - On Windows: .\\env\\Scripts\\activate")
        print("   - On macOS/Linux: source env/bin/activate")
        print("3. Set the environment variables in the virtual environment:")
        print("   - On Windows: set DUO_IKEY=<your-integration-key>")
        print("                 set DUO_SKEY=<your-secret-key>")
        print("                 set DUO_HOST=<your-api-hostname>")
        print("   - On macOS/Linux: export DUO_IKEY=<your-integration-key>")
        print("                     export DUO_SKEY=<your-secret-key>")
        print("                     export DUO_HOST=<your-api-hostname>")
        exit(1)
    
    return ikey, skey, host


def parse_arguments():
    """Parse command-line arguments for the child account details and desired limit"""
    parser = argparse.ArgumentParser(description="Set hard user limit for a Duo subaccount.")
    parser.add_argument('account_id', type=str, help='Child account ID')
    parser.add_argument('child_api_host', type=str, help='Child account API hostname')
    parser.add_argument('desired_limit', type=int, help='Desired hard user limit to apply to subaccount')

    args = parser.parse_args()

    if args.desired_limit < 0:
        parser.error("Invalid limit. Please select a value 0 or higher")

    return args.account_id, args.child_api_host, args.desired_limit


def main():
    """Main program entry point"""

    ikey, skey, host = check_environment_variables()
    account_id, child_api_host, desired_limit = parse_arguments()

    # Initialize the custom admin class with the credentials
    account_admin_api = CustomDuoAdmin(
        ikey=ikey,
        skey=skey,
        host=host,
        account_id=account_id
    )

    print(f"Setting hard user limit for account ID {account_id} to {desired_limit}")

    # Set the hard user limit using the custom method
    try:
        result = account_admin_api.set_user_limit(account_id, str(desired_limit))  # Convert to string
        if 'stat' in result and result['stat'] == 'OK':
            print(f"Hard user limit of [{desired_limit}] successfully set for account ID {account_id}")
        else:
            print(f"An error occurred while setting hard user limit for account {account_id}")
            print(f"Error message: {result}")
    except Exception as e:
        print(f"An exception occurred: {e}")

if __name__ == '__main__':
    main()