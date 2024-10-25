import duo_client
import getpass

class CustomDuoAdmin(duo_client.admin.AccountAdmin):
    def set_user_limit(self, account_id, desired_hard_limit):
        """Method to call the hidden /admin/v1/billing/user_limit endpoint to set user limit"""
        endpoint = '/admin/v1/billing/user_limit'
        params = {
            'account_id': account_id,
            'desired_hard_limit': str(desired_hard_limit)  # Convert to string
        }
        response = self.json_api_call('POST', endpoint, params)
        return response


def _get_user_input(prompt, secure=False):
    """Read information from STDIN, using getpass when sensitive information should not be echoed to tty"""
    if secure is True:
        return getpass.getpass(prompt)
    else:
        return input(prompt)


def prompt_for_credentials() -> dict:
    """Collect required API credentials from command line prompts"""

    ikey = _get_user_input('Duo Accounts API integration key ("DI..."): ')
    skey = _get_user_input('Duo Accounts API integration secret key: ', secure=True)
    host = _get_user_input('Duo Accounts API hostname ("api-....duosecurity.com"): ')
    account_id = _get_user_input('Child account ID: ')
    account_apihost = _get_user_input('Child account api_hostname: ')
    desired_limit = int(_get_user_input('Desired hard user limit to apply to subaccount: '))
    while desired_limit < 0:
        print(f"Invalid limit. Please select a value 0 or higher")
        desired_limit = int(_get_user_input('Desired hard user limit to apply to subaccount: '))

    return {
            "ikey": ikey,
            "skey": skey,
            "host": host,
            "account_id": account_id,
            "child_api_host": account_apihost,
            "desired_limit": desired_limit,
    }

def main():
    """Main program entry point"""

    inputs = prompt_for_credentials()

    # Initialize the custom admin class with the credentials
    account_admin_api = CustomDuoAdmin(
        ikey=inputs['ikey'],
        skey=inputs['skey'],
        host=inputs['host'],
        account_id=inputs['account_id']
    )

    print(f"Setting hard user limit for account ID {inputs['account_id']} to {inputs['desired_limit']}")

    # Set the hard user limit using the custom method
    try:
        result = account_admin_api.set_user_limit(inputs['account_id'], str(inputs['desired_limit']))  # Convert to string
        if 'stat' in result and result['stat'] == 'OK':
            print(f"Hard user limit of [{inputs['desired_limit']}] successfully set for account ID {inputs['account_id']}")
        else:
            print(f"An error occurred while setting hard user limit for account {inputs['account_id']}")
            print(f"Error message: {result}")
    except Exception as e:
        print(f"An exception occurred: {e}")

if __name__ == '__main__':
    main()