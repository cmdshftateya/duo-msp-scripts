import duo_client
import getpass

def prompt_for_credentials() -> dict:
    """Collect required API credentials and account name from a single input line

    :return: dictionary containing Duo Accounts API ikey, skey, host, and account name
    """
    user_input = input('Enter the integration key, secret key, API hostname, and account name separated by spaces:\n')
    ikey, skey, host, account_name = user_input.split()

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