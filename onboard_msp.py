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
    
def main():
    """Main program entry point"""
    

if __name__ == '__main__':
    main()