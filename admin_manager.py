#!/usr/bin/env python3
"""
Duo Security Admin Manager Script

This script manages Duo Security admins by listing existing admins, creating new ones, or updating existing ones.

Required environment variables:
- DUO_PARENT_IKEY: Parent Admin API integration key
- DUO_PARENT_SKEY: Parent Admin API secret key
- DUO_PARENT_HOST: Parent Admin API hostname
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
    
    def update_admin(self, admin_id, name=None, phone=None, role=None, subaccount_role=None):
        """Method to update an admin
        
        Args:
            admin_id (str): The ID of the admin to update
            name (str, optional): New name for the admin
            phone (str, optional): New phone number for the admin
            role (str, optional): New role for the admin
            subaccount_role (str, optional): New subaccount role for the admin
            
        Returns:
            dict: The updated admin information
        """
        endpoint = f'/admin/v1/admins/{admin_id}'
        params = {}
        
        if name:
            params['name'] = name
        
        if phone:
            params['phone'] = phone
        
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
        
        if subaccount_role:
            subaccount_role_mapping = {
                "owner": "Owner",
                "administrator": "Administrator",
                "application manager": "Application Manager",
                "user manager": "User Manager",
                "help desk": "Help Desk",
                "read-only": "Read-only",
                "billing": "Billing"
            }
            params['subaccount_role'] = subaccount_role_mapping.get(subaccount_role.lower(), subaccount_role)
        
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
        'DUO_PARENT_IKEY': 'Admin API integration key',
        'DUO_PARENT_SKEY': 'Admin API secret key',
        'DUO_PARENT_HOST': 'Admin API hostname'
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
            ikey=os.environ['DUO_PARENT_IKEY'],
            skey=os.environ['DUO_PARENT_SKEY'],
            host=os.environ['DUO_PARENT_HOST']
        )
        
        print("\nConnected to Duo Security API")
        
        while True:
            print("\nAvailable commands:")
            print("1. get_admins - List all admins")
            print("2. create_admin - Create a new admin")
            print("3. update_admin - Update an existing admin")
            print("4. exit - Exit the program")
            
            command = input("\nEnter command: ").strip().lower()
            
            if command in ['exit', '4', 'q', 'quit']:
                print("Exiting program.")
                sys.exit(0)
            
            elif command in ['get_admins', '1', 'list', 'ls']:
                try:
                    start_time = time.time()
                    admins = admin_manager.get_admins()
                    
                    # Prepare data for table format
                    table_data = []
                    headers = ["Admin ID", "Name", "Role", "Email", "Status", "Last Login"]
                    
                    for admin in admins:
                        admin_id = admin.get('admin_id', 'N/A')
                        name = admin.get('name', 'N/A')
                        role = admin.get('role', 'N/A')
                        email = admin.get('email', 'N/A')
                        status = admin.get('status', 'N/A')
                        last_login = format_timestamp(admin.get('last_login_time'))
                        
                        table_data.append([admin_id, name, role, email, status, last_login])
                    
                    # Sort by name for readability
                    table_data.sort(key=lambda x: x[1].lower())
                    
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
                    print(f"Admin ID: {result.get('admin_id')}")
                    
                except Exception as e:
                    print(f"Error: {e}")
            
            elif command in ['update_admin', '3', 'update', 'edit']:
                try:
                    # First list all admins for selection
                    admins = admin_manager.get_admins()
                    
                    # Prepare data for table format
                    table_data = []
                    headers = ["#", "Admin ID", "Name", "Role", "Email"]
                    
                    for i, admin in enumerate(admins, 1):
                        admin_id = admin.get('admin_id', 'N/A')
                        name = admin.get('name', 'N/A')
                        role = admin.get('role', 'N/A')
                        email = admin.get('email', 'N/A')
                        
                        table_data.append([i, admin_id, name, role, email])
                    
                    # Sort by name for readability
                    table_data.sort(key=lambda x: x[2].lower())
                    
                    # Display table
                    print("\nSelect an admin to update:")
                    print(format_table(table_data, headers))
                    
                    admin_choice = input("\nSelect admin (number or admin_id): ")
                    
                    # Find selected admin
                    selected_admin = None
                    if admin_choice.isdigit() and 1 <= int(admin_choice) <= len(admins):
                        # User selected by number
                        selected_admin = admins[int(admin_choice) - 1]
                    else:
                        # User selected by admin_id
                        for admin in admins:
                            if admin.get('admin_id') == admin_choice:
                                selected_admin = admin
                                break
                    
                    if not selected_admin:
                        print("Invalid selection. Please try again.")
                        continue
                    
                    print(f"\nUpdating admin: {selected_admin.get('name')} ({selected_admin.get('email')})")
                    admin_id = selected_admin.get('admin_id')
                    
                    # Get update fields
                    print("Enter new values (press Enter to keep current values):")
                    name = input(f"Name [{selected_admin.get('name')}]: ") or None
                    phone = input(f"Phone [{selected_admin.get('phone', 'N/A')}]: ") or None
                    
                    # Roles
                    print("\nAvailable roles:")
                    roles = ["Owner", "Administrator", "Application Manager", "User Manager", 
                            "Help Desk", "Read-only", "Security Analyst"]
                    
                    for i, role in enumerate(roles, 1):
                        print(f"{i}. {role}")
                    
                    role_input = input(f"\nSelect role [{selected_admin.get('role', 'N/A')}] (number or name, press Enter to skip): ")
                    
                    # Process role input (either number or text)
                    role = None
                    if role_input:
                        if role_input.isdigit() and 1 <= int(role_input) <= len(roles):
                            role = roles[int(role_input) - 1]
                        else:
                            role = role_input
                    
                    # Subaccount roles
                    print("\nAvailable subaccount roles:")
                    subaccount_roles = ["Owner", "Administrator", "Application Manager", "User Manager", 
                                       "Help Desk", "Read-only", "Billing"]
                    
                    for i, role in enumerate(subaccount_roles, 1):
                        print(f"{i}. {role}")
                    
                    subaccount_role_input = input(f"\nSelect subaccount role " +
                                                 f"[{selected_admin.get('subaccount_role', 'N/A')}] " +
                                                 "(number or name, press Enter to skip): ")
                    
                    # Process subaccount role input (either number or text)
                    subaccount_role = None
                    if subaccount_role_input:
                        if subaccount_role_input.isdigit() and 1 <= int(subaccount_role_input) <= len(subaccount_roles):
                            subaccount_role = subaccount_roles[int(subaccount_role_input) - 1]
                        else:
                            subaccount_role = subaccount_role_input
                    
                    # Confirm update
                    print("\nUpdate summary:")
                    if name:
                        print(f"- Name: {selected_admin.get('name')} -> {name}")
                    if phone:
                        print(f"- Phone: {selected_admin.get('phone', 'N/A')} -> {phone}")
                    if role:
                        print(f"- Role: {selected_admin.get('role', 'N/A')} -> {role}")
                    if subaccount_role:
                        print(f"- Subaccount Role: {selected_admin.get('subaccount_role', 'N/A')} -> {subaccount_role}")
                    
                    confirm = input("\nConfirm update (y/n)? ").lower()
                    if confirm not in ['y', 'yes']:
                        print("Update cancelled.")
                        continue
                    
                    # Perform update
                    result = admin_manager.update_admin(
                        admin_id, 
                        name=name, 
                        phone=phone, 
                        role=role, 
                        subaccount_role=subaccount_role
                    )
                    
                    print(f"Admin updated successfully: {result.get('name')} ({result.get('email')})")
                    
                except Exception as e:
                    print(f"Error: {e}")
            
            else:
                print(f"Unknown command: {command}")
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()