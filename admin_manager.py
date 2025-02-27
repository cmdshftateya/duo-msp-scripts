#!/usr/bin/env python3
"""
Duo Security Admin Manager Script

This script manages Duo Security admins by listing existing admins or creating new ones.

Required environment variables:
- DUO_IKEY: Admin API integration key
- DUO_SKEY: Admin API secret key
- DUO_HOST: Admin API hostname
"""

import os
import sys
import duo_client
from datetime import datetime
import time

class AdminManager(duo_client.Admin):
    """Class for managing Duo Security admins"""
    
    def get_admins(self):
        """Method to get all admins"""
        endpoint = '/admin/v1/admins'
        response = self.json_api_call('GET', endpoint, {})
        return response
    
    def create_admin(self, name, email, phone, role=None):
        """Method to create an admin"""
        endpoint = '/admin/v1/admins'
        params = {
            'name': name,
            'email': email,
            'phone': phone
        }
        
        if role:
            # Convert to API expected format (proper capitalization)
            role_mapping = {
                "owner": "Owner",
                "administrator": "Administrator",
                "application manager": "Application Manager",
                "user manager": "User Manager",
                "help desk": "Help Desk",
                "read-only": "Read-only",
                "security analyst": "Security Analyst"
            }
            params['role'] = role_mapping.get(role.lower(), role)
            
        response = self.json_api_call('POST', endpoint, params)
        return response

def format_timestamp(timestamp):
    """Convert Unix timestamp to readable date format"""
    if not timestamp:
        return "Never"
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

def format_table(data, headers, widths=None):
    """Format data into a table with proper alignment"""
    if not data:
        return "No data available"
    
    # Determine column widths if not provided
    if not widths:
        widths = []
        for i, header in enumerate(headers):
            col_data = [str(row[i]) for row in data]
            col_data.append(header)
            widths.append(max(len(s) for s in col_data))
    
    # Create header row
    header_row = " | ".join(h.ljust(w) for h, w in zip(headers, widths))
    separator = "-+-".join("-" * w for w in widths)
    
    # Format data rows
    table_rows = [header_row, separator]
    for row in data:
        formatted_row = " | ".join(str(cell).ljust(w) for cell, w in zip(row, widths))
        table_rows.append(formatted_row)
    
    return "\n".join(table_rows)

def main():
    print("Duo Security Admin Manager")
    print("--------------------------")
    
    # Load credentials from environment variables
    required_vars = {
        'DUO_IKEY': 'Admin API integration key',
        'DUO_SKEY': 'Admin API secret key',
        'DUO_HOST': 'Admin API hostname'
    }
    
    missing_vars = [var for var, desc in required_vars.items() if not os.environ.get(var)]
    if missing_vars:
        print("Error: The following required environment variables are not set:")
        for var in missing_vars:
            print(f"- {var} ({required_vars[var]})")
        print("Please set these variables and try again.")
        sys.exit(1)
    
    try:
        # Initialize AdminManager with environment variables
        admin_manager = AdminManager(
            ikey=os.environ['DUO_IKEY'],
            skey=os.environ['DUO_SKEY'],
            host=os.environ['DUO_HOST']
        )
        
        print("\nConnected to Duo Security API")
        
        while True:
            print("\nAvailable commands:")
            print("1. get_admins - List all admins")
            print("2. create_admin - Create a new admin")
            print("3. exit - Exit the program")
            
            command = input("\nEnter command: ").strip().lower()
            
            if command in ['exit', '3', 'q', 'quit']:
                print("Exiting program.")
                sys.exit(0)
            
            elif command in ['get_admins', '1', 'list', 'ls']:
                try:
                    start_time = time.time()
                    admins = admin_manager.get_admins()
                    
                    # Prepare data for table format
                    table_data = []
                    headers = ["Name", "Role", "Email", "Status", "Last Login"]
                    
                    for admin in admins:
                        name = admin.get('name', 'N/A')
                        role = admin.get('role', 'N/A')
                        email = admin.get('email', 'N/A')
                        status = admin.get('status', 'N/A')
                        last_login = format_timestamp(admin.get('last_login_time'))
                        
                        table_data.append([name, role, email, status, last_login])
                    
                    # Sort by name for readability
                    table_data.sort(key=lambda x: x[0].lower())
                    
                    # Display table
                    print(f"\n{format_table(table_data, headers)}")
                    
                    end_time = time.time()
                    print(f"\nRetrieved {len(admins)} admins in {end_time - start_time:.2f} seconds")
                except Exception as e:
                    print(f"Error: {e}")
            
            elif command in ['create_admin', '2', 'create', 'add']:
                try:
                    name = input("Admin name: ")
                    email = input("Admin email: ")
                    phone = input("Admin phone: ")
                    
                    print("\nAvailable roles:")
                    roles = ["Owner", "Administrator", "Application Manager", "User Manager", 
                            "Help Desk", "Read-only", "Security Analyst"]
                    
                    for i, role in enumerate(roles, 1):
                        print(f"{i}. {role}")
                    
                    role_input = input("\nSelect role (number or name, press Enter to skip): ")
                    
                    # Process role input (either number or text)
                    role = None
                    if role_input:
                        if role_input.isdigit() and 1 <= int(role_input) <= len(roles):
                            role = roles[int(role_input) - 1]
                        else:
                            role = role_input
                    
                    result = admin_manager.create_admin(name, email, phone, role)
                    print(f"Admin created successfully: {result.get('name')} ({result.get('email')})")
                except Exception as e:
                    print(f"Error: {e}")
            
            else:
                print("Unknown command. Please enter a valid option.")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()