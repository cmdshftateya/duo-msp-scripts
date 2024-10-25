"""
In progress development to create a easily usable file to set hard user limit on subaccounts
"""

import argparse
import duo_client
import getpass

class CustomDuoAdmin(duo_client.Admin):
    def set_user_limit(self, account_id, desired_hard_limit):
        """Method to call the hidden /admin/v1/billing/user_limit endpoint to set user limit"""
        endpoint = '/admin/v1/billing/user_limit'
        params = {
            'account_id': account_id,
            'desired_hard_limit': desired_hard_limit
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
    account_edition = _get_user_input('Child account edition: ')
    while account_edition.upper() not in ALLOWED_DUO_EDITIONS:
        print(f"Invalid account edition. Please select one of {ALLOWED_DUO_EDITIONS}")
        account_edition = _get_user_input('Child account edition: ')

    return {
            "ikey": ikey,
            "skey": skey,
            "host": host,
            "account_id": account_id,
            "child_api_host": account_apihost,
            "account_edition": account_edition,
    }

# It is important to note that we are using the IKEY/SKEY combination for an Accounts API integration in the
# parent account along with the api-hostname of a child account to create a new duo_client.Admin instance
account_client = duo_client.Admin(
        ikey=args.ikey,
        skey=args.skey,
        host=args.host,
)

# Once the duo_client.Admin instance is created, the child account_id is assigned. This is necessary to ensure
# queries made with this Admin API instance are directed to the proper child account that matches the api-hostname
# used to create the instance.
account_client.account_id = args.child_account_id


def main():
    """Main program entry point"""

    inputs = prompt_for_credentials()
    edition = inputs.pop('account_edition')
    edition = edition.upper()

    account_admin_api = duo_client.admin.AccountAdmin(**inputs)

    print(f"Setting edition for account ID {inputs['account_id']} to {edition}")
    result = account_admin_api.set_edition(edition)
    if result != "":
        print(f"An error occurred while setting edition for account {inputs['account_id']}")
        print(f"Error message: {result}")
    else:
        print(f"Edition [{edition}] successfully set for account ID {inputs['account_id']}")


if __name__ == '__main__':
    main()

