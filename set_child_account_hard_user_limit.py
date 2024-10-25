"""
In progress development to create a easily usable file to set hard user limit on subaccounts
"""

import argparse
import duo_client
import getpass

# class CustomDuoAdmin(duo_client.Admin):
#     def set_user_limit(self, account_id, desired_hard_limit):
#         """Method to call the hidden /admin/v1/billing/user_limit endpoint to set user limit"""
#         endpoint = '/admin/v1/billing/user_limit'
#         params = {
#             'account_id': account_id,
#             'desired_hard_limit': desired_hard_limit
#         }
#         response = self.json_api_call('POST', endpoint, params)
#         return response

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
    desired_limit = _get_user_input('Desired hard user limit to apply to subaccount: ')
    while desired_limit < 0:
        print(f"Invalid limit. Please select a value 0 or higher")
        desired_limit = _get_user_input('Desired hard user limit to apply to subaccount: ')

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

    account_admin_api = duo_client.admin.AccountAdmin(**inputs)

    print(f"Setting hard user limit for account ID {inputs['account_id']} to {inputs['desired_limit']}")
    # TODO: make the following line possible
    result = account_admin_api.set_hard_user_limit(inputs['desired_limit'])
    if result != "":
        print(f"An error occurred while setting hard user limit for account {inputs['account_id']}")
        print(f"Error message: {result}")
    else:
        print(f"Hard user limit of [{inputs['desired_limit']}] successfully set for account ID {inputs['account_id']}")


if __name__ == '__main__':
    main()

