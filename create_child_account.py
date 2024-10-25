"""
Example of Duo Accounts API child account creation
"""

import duo_client
import os
import sys
import getpass
from pprint import pprint


argv_iter = iter(sys.argv[1:])


def _get_next_arg(prompt, secure=False):
    """Read information from STDIN, using getpass when sensitive information should not be echoed to tty"""
    try:
        return next(argv_iter)
    except StopIteration:
        if secure is True:
            return getpass.getpass(prompt)
        else:
            return input(prompt)


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


def prompt_for_credentials() -> dict:
    """Collect required API credentials from command line prompts or environment variables

    :return: dictionary containing Duo Accounts API ikey, skey, and hostname strings, and account name
    """
    ikey, skey, host = check_environment_variables()
    account_name = _get_next_arg('Name for new child account: ')

    return {"IKEY": ikey, "SKEY": skey, "APIHOST": host, "ACCOUNT_NAME": account_name}


def main():
    """Main program entry point"""

    inputs = prompt_for_credentials()

    account_client = duo_client.Accounts(
            ikey=inputs['IKEY'],
            skey=inputs['SKEY'],
            host=inputs['APIHOST']
    )

    print(f"Creating child account with name [{inputs['ACCOUNT_NAME']}]")
    child_account = account_client.create_account(inputs['ACCOUNT_NAME'])

    if 'account_id' in child_account:
        print(f"Child account for [{inputs['ACCOUNT_NAME']}] created successfully.")
    else:
        print(f"An unexpected error occurred while creating child account for {inputs['ACCOUNT_NAME']}")
    print(child_account)


if __name__ == '__main__':
    main()