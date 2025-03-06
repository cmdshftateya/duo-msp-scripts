import os
import sys
import duo_client
from datetime import datetime
import time

class AdminManager(duo_client.Admin):
    """Class for managing Duo Security admins"""
    
    def get_admins(self):
        return self.json_api_call('GET', '/admin/v1/admins', {})
    
    def create_admin(self, name, email, phone, role=None):
        params = {'name': name, 'email': email, 'phone': phone}
        if role:
            params['role'] = self.map_role(role)
        return self.json_api_call('POST', '/admin/v1/admins', params)
    
    def update_admin(self, admin_id, name=None, phone=None, role=None, subaccount_role=None):
        params = {k: v for k, v in [('name', name), ('phone', phone), ('role', self.map_role(role)), ('subaccount_role', self.map_subaccount_role(subaccount_role))] if v}
        return self.json_api_call('POST', f'/admin/v1/admins/{admin_id}', params)
    
    def sync_admin(self, directory_key, email):
        params = {'email': email}
        return self.json_api_call('POST', f'/admin/v1/admins/directorysync/{directory_key}/syncadmin', params)
    
    def map_role(self, role):
        role_mapping = {
            "owner": "Owner", "administrator": "Administrator", "application manager": "Application Manager",
            "user manager": "User Manager", "help desk": "Help Desk", "read-only": "Read-only", "security analyst": "Security Analyst"
        }
        return role_mapping.get(role.lower(), role) if role else None
    
    def map_subaccount_role(self, subaccount_role):
        subaccount_role_mapping = {
            "administrator": "Administrator", "application manager": "Application Manager", "user manager": "User Manager",
            "help desk": "Help Desk", "read-only": "Read-only", "billing": "Billing"
        }
        return subaccount_role_mapping.get(subaccount_role.lower(), subaccount_role) if subaccount_role else None

def format_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp else "Never"

def format_table(data, headers):
    if not data:
        return "No data available"
    widths = [max(len(str(row[i])) for row in data + [headers]) for i in range(len(headers))]
    separator = "-+-".join("-" * w for w in widths)
    table = [" | ".join(h.ljust(w) for h, w in zip(headers, widths)), separator]
    table.extend(" | ".join(str(cell).ljust(w) for cell, w in zip(row, widths)) for row in data)
    return "\n".join(table)

def get_admin_input():
    return input("\nEnter command: ").strip().lower()

def list_admins(admin_manager):
    try:
        admins = admin_manager.get_admins()
        headers = ["Admin ID", "Name", "Role", "Subaccount Role", "Email", "Status", "Last Login"]
        table_data = [[a.get('admin_id', 'N/A'), a.get('name', 'N/A'), a.get('role', 'N/A'),
                       a.get('subaccount_role', 'N/A'), a.get('email', 'N/A'), a.get('status', 'N/A'),
                       format_timestamp(a.get('last_login_time'))] for a in admins]
        print(f"\n{format_table(table_data, headers)}\nRetrieved {len(admins)} admins")
    except Exception as e:
        print(f"Error: {e}")

def create_admin(admin_manager):
    try:
        name, email, phone = input("Admin name: "), input("Admin email: "), input("Admin phone: ")
        role = input("Select role (press Enter to skip): ").strip()
        result = admin_manager.create_admin(name, email, phone, role or None)
        print(f"Admin created: {result.get('name')} ({result.get('email')})")
    except Exception as e:
        print(f"Error: {e}")

def update_admin(admin_manager):
    try:
        list_admins(admin_manager)
        admin_id = input("\nEnter Admin ID to update: ").strip()
        name, phone = input("New name (Enter to skip): ") or None, input("New phone (Enter to skip): ") or None
        role = input("New role (Enter to skip): ").strip() or None
        subaccount_role = input("New subaccount role (Enter to skip): ").strip() or None
        result = admin_manager.update_admin(admin_id, name, phone, role, subaccount_role)
        print(f"Admin updated: {result.get('name')} ({result.get('email')})")
    except Exception as e:
        print(f"Error: {e}")

def sync_admin(admin_manager):
    try:
        directory_key = input("Enter Directory Key: ").strip()
        email = input("Enter Admin Email: ").strip()
        result = admin_manager.sync_admin(directory_key, email)
        print(f"Sync Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Duo Security Admin Manager\n--------------------------")
    required_vars = ['DUO_PARENT_IKEY', 'DUO_PARENT_SKEY', 'DUO_PARENT_HOST']
    if missing := [var for var in required_vars if not os.environ.get(var)]:
        print("Error: Missing environment variables:", ", ".join(missing))
        sys.exit(1)
    
    admin_manager = AdminManager(os.environ['DUO_PARENT_IKEY'], os.environ['DUO_PARENT_SKEY'], os.environ['DUO_PARENT_HOST'])
    print("Connected to Duo Security API")
    
    commands = {"get_admins": list_admins, "create_admin": create_admin, "update_admin": update_admin, "sync_admin": sync_admin}
    
    while True:
        print("\nCommands: get_admins, create_admin, update_admin, sync_admin, exit")
        command = get_admin_input()
        if command in ["exit", "quit"]:
            print("Exiting program.")
            sys.exit(0)
        elif command in commands:
            commands[command](admin_manager)
        else:
            print("Unknown command.")

if __name__ == "__main__":
    main()