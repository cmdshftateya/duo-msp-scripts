#!/usr/bin/env python3
"""
Duo Security Account Reporting Script

This script generates a comprehensive report of users across a Duo Security parent account
and all associated subaccounts, using both the Admin API and Accounts API.

Configuration:
    The script requires a duo.conf file with the following credentials:
    - DUO_PARENT_IKEY: Parent Admin API integration key
    - DUO_PARENT_SKEY: Parent Admin API secret key
    - DUO_PARENT_HOST: Parent Admin API hostname
    - DUO_ACCOUNTS_IKEY: Accounts API integration key
    - DUO_ACCOUNTS_SKEY: Accounts API secret key
    - DUO_ACCOUNTS_HOST: Accounts API hostname
"""

import os
import sys
from datetime import datetime, timezone
import time
import pandas as pd
from tabulate import tabulate

import duo_client

def load_config():
    """Load configuration from duo.conf file."""
    config = {}
    try:
        with open('duo.conf', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except FileNotFoundError:
        print("Error: duo.conf file not found. Please create it with your Duo Security API credentials.")
        sys.exit(1)
    
    required_keys = [
        'DUO_PARENT_IKEY', 'DUO_PARENT_SKEY', 'DUO_PARENT_HOST',
        'DUO_ACCOUNTS_IKEY', 'DUO_ACCOUNTS_SKEY', 'DUO_ACCOUNTS_HOST'
    ]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        print(f"Error: Missing required credentials in duo.conf: {', '.join(missing_keys)}")
        sys.exit(1)
    
    return config

def human_time(timestamp):
    """Translate unix time into human readable string."""
    if timestamp is None:
        return 'Never'
    return datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def get_parent_account_name(admin_client):
    """Get the parent account name from settings."""
    try:
        settings = admin_client.get_settings()
        return settings.get('name', 'Parent Account')
    except Exception as e:
        print(f"Error getting parent account name: {e}")
        return "Parent Account"

def get_user_details(admin_client, account_name, account_id=None):
    """Get detailed user information from an account."""
    print(f"Fetching users for account: {account_name}")
    params = {}
    if account_id:
        params['account_id'] = account_id
    
    try:
        # Get all users
        users_response = admin_client.json_api_call('GET', '/admin/v1/users', params)
        users = []
        
        for user in users_response:
            user_id = user['user_id']
            
            # Get phones for this user
            phones_response = admin_client.json_api_call('GET', f'/admin/v1/users/{user_id}/phones', params)
            phone_numbers = [f"{p['number']} ({p['type']})" for p in phones_response]
            
            # Get tokens for this user
            tokens_response = admin_client.json_api_call('GET', f'/admin/v1/users/{user_id}/tokens', params)
            token_types = [t['type'] for t in tokens_response]
            
            # Get last login time
            last_login = human_time(user.get('last_login'))
            
            users.append({
                'account': account_name,
                'username': user.get('username', ''),
                'name': f"{user.get('firstname', '')} {user.get('lastname', '')}".strip(),
                'email': user.get('email', ''),
                'status': user.get('status', ''),
                'phones': ', '.join(phone_numbers) if phone_numbers else 'None',
                'tokens': ', '.join(token_types) if token_types else 'None',
                'last_login': last_login,
                'enrolled': user.get('is_enrolled', False)
            })
        
        return users
    
    except Exception as e:
        print(f"Error getting user details for {account_name}: {e}")
        return []

def get_subaccounts(accounts_client):
    """Get all subaccounts using the Accounts API."""
    try:
        accounts = accounts_client.get_child_accounts()
        return accounts
    except Exception as e:
        print(f"Error getting subaccounts: {e}")
        return []

def main():
    print("Duo Security MSP User Report")
    print("===========================")
    
    # Load configuration from duo.conf
    config = load_config()
    
    # Initialize API clients
    parent_admin_client = duo_client.Admin(
        ikey=config['DUO_PARENT_IKEY'],
        skey=config['DUO_PARENT_SKEY'],
        host=config['DUO_PARENT_HOST']
    )
    
    accounts_client = duo_client.Accounts(
        ikey=config['DUO_ACCOUNTS_IKEY'],
        skey=config['DUO_ACCOUNTS_SKEY'],
        host=config['DUO_ACCOUNTS_HOST']
    )
    
    all_users = []
    
    # Get parent account name and users
    parent_account_name = get_parent_account_name(parent_admin_client)
    parent_users = get_user_details(parent_admin_client, parent_account_name)
    all_users.extend(parent_users)
    print(f"Found {len(parent_users)} users in parent account")
    
    # Get subaccounts
    subaccounts = get_subaccounts(accounts_client)
    print(f"Found {len(subaccounts)} subaccounts")
    
    # Process each subaccount
    for subaccount in subaccounts:
        account_id = subaccount['account_id']
        account_name = subaccount['name']
        api_hostname = subaccount['api_hostname']
        
        print(f"Processing subaccount: {account_name} ({account_id})")
        
        # Create admin client for this subaccount using Accounts API credentials
        subaccount_admin_client = duo_client.Admin(
            ikey=accounts_client.ikey,
            skey=accounts_client.skey,
            host=api_hostname
        )
        
        # Get users for this subaccount
        subaccount_users = get_user_details(subaccount_admin_client, account_name, account_id=account_id)
        all_users.extend(subaccount_users)
        print(f"Found {len(subaccount_users)} users in subaccount {account_name}")
        
        # Sleep to avoid rate limiting
        time.sleep(1)
    
    # Convert to DataFrame for easier handling
    df = pd.DataFrame(all_users)
    
    # Print table
    if not df.empty:
        # Reorder columns for better readability
        columns = ['account', 'username', 'name', 'email', 'status', 'phones', 'tokens', 'last_login', 'enrolled']
        df = df[columns]
        
        print("\nUser Report Across All Duo Security Accounts:")
        table = tabulate(df, headers='keys', tablefmt='grid', showindex=False)
        print(table)
        
        # Save to CSV
        csv_filename = f"duo_security_user_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"\nReport saved to {csv_filename}")
    else:
        print("No users found across all accounts")

if __name__ == "__main__":
    main()