import duo_client

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


def prompt_for_credentials():
    """Prompt user for all required inputs"""
    user_input = input('Enter ikey, skey, host, mode (get/set), account_id, child_api_host, and desired_limit (for set mode only) separated by spaces:\n')
    inputs = user_input.split()

    if len(inputs) < 6:
        raise ValueError("Insufficient arguments provided. Expected at least 6 arguments.")

    ikey, skey, host, mode, account_id, child_api_host = inputs[:6]
    desired_limit = int(inputs[6]) if mode == 'set' and len(inputs) > 6 else None

    if mode == 'set' and desired_limit is None:
        raise ValueError("desired_limit is required when mode is set")

    if desired_limit is not None and desired_limit < 0:
        raise ValueError("Invalid limit. Please select a value 0 or higher")

    return ikey, skey, host, mode, account_id, child_api_host, desired_limit


def main():
    """Main program entry point"""
    try:
        ikey, skey, host, mode, account_id, child_api_host, desired_limit = prompt_for_credentials()
        
        # Initialize the custom admin class with the credentials
        account_admin_api = CustomDuoAdmin(
            ikey=ikey,
            skey=skey,
            host=host,
            account_id=account_id
        )

        if mode == 'set':
            print(f"Setting hard user limit for account ID {account_id} to {desired_limit}")
            # Set the hard user limit using the custom method
            result = account_admin_api.set_user_limit(account_id, str(desired_limit))
        elif mode == 'get':
            print(f"Getting hard user limit for account ID {account_id}")
            # Get the hard user limit using the custom method
            result = account_admin_api.get_user_limit(account_id)

        print(result)
    except Exception as e:
        print(f"An error occurred: {e}")
        # You can add more sophisticated error handling here

if __name__ == '__main__':
    main()