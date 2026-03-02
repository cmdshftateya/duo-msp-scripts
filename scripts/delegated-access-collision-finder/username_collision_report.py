#!/usr/bin/env python3
"""
Duo Security Username Collision Report Script

This script identifies username and alias collisions between a Duo Security parent account
and all associated subaccounts. It generates a comprehensive report showing which usernames
or aliases from the parent account exist in any subaccount.

Configuration:
    The script requires a duo.conf file with the following credentials:
    - DUO_PARENT_IKEY: Parent Admin API integration key
    - DUO_PARENT_SKEY: Parent Admin API secret key
    - DUO_PARENT_HOST: Parent Admin API hostname
    - DUO_ACCOUNTS_IKEY: Accounts API integration key
    - DUO_ACCOUNTS_SKEY: Accounts API secret key
    - DUO_ACCOUNTS_HOST: Accounts API hostname

Output:
    - Console: Summary statistics and collision overview
    - CSV: Detailed collision data (username_collision_report_YYYYMMDD_HHMMSS.csv)
    - PDF: Professional formatted report (username_collision_report_YYYYMMDD_HHMMSS.pdf)
"""

import os
import sys
from datetime import datetime, timezone
import time
import pandas as pd
from tabulate import tabulate
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

import duo_client


def load_config():
    """Load configuration from duo.conf file."""
    config = {}
    try:
        with open('duo.conf', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
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


def get_parent_users(admin_client):
    """Get all users from parent account with their aliases."""
    print("Fetching users from parent account...")
    try:
        users_response = admin_client.json_api_call('GET', '/admin/v1/users', {})

        parent_users = {}
        for user in users_response:
            user_id = user.get('user_id')
            username = user.get('username', '')
            aliases = user.get('aliases', [])

            parent_users[user_id] = {
                'user_id': user_id,
                'username': username,
                'aliases': aliases,
                'identifiers': {username} | set(aliases)
            }

        print(f"Found {len(parent_users)} users in parent account")
        return parent_users

    except Exception as e:
        print(f"Error getting parent users: {e}")
        sys.exit(1)


def get_subaccounts_with_users(accounts_client, user_agent=None):
    """Get all subaccounts and their users."""
    print("Fetching subaccounts...")
    try:
        subaccounts = accounts_client.get_child_accounts()
        print(f"Found {len(subaccounts)} subaccounts")
    except Exception as e:
        print(f"Error getting subaccounts: {e}")
        return []

    subaccounts_data = []

    for subaccount in subaccounts:
        account_id = subaccount['account_id']
        account_name = subaccount['name']
        api_hostname = subaccount['api_hostname']

        print(f"Fetching users from subaccount: {account_name}...")

        try:
            # Create admin client for this subaccount using Accounts API credentials
            admin_kwargs = {
                'ikey': accounts_client.ikey,
                'skey': accounts_client.skey,
                'host': api_hostname
            }
            if user_agent:
                admin_kwargs['user_agent'] = user_agent

            subaccount_admin_client = duo_client.Admin(**admin_kwargs)

            # Get users for this subaccount
            params = {'account_id': account_id}
            users_response = subaccount_admin_client.json_api_call('GET', '/admin/v1/users', params)

            # Build user lookup dictionary
            users_dict = {}
            for user in users_response:
                username = user.get('username', '')
                aliases = user.get('aliases', [])

                users_dict[username] = {
                    'username': username,
                    'aliases': aliases,
                    'identifiers': {username} | set(aliases)
                }

            subaccounts_data.append({
                'account_id': account_id,
                'account_name': account_name,
                'users': users_dict
            })

            print(f"  Found {len(users_dict)} users in {account_name}")

        except Exception as e:
            print(f"  Error getting users for {account_name}: {e}")
            continue

    return subaccounts_data


def detect_collisions(parent_users, subaccounts_data):
    """Detect collisions between parent users and subaccount users."""
    print("\nDetecting collisions...")

    collisions = []
    users_with_collisions = set()
    users_without_collisions = []

    for user_id, parent_user in parent_users.items():
        parent_username = parent_user['username']
        parent_identifiers = parent_user['identifiers']
        user_has_collision = False

        for subaccount in subaccounts_data:
            account_name = subaccount['account_name']
            account_id = subaccount['account_id']

            for sub_username, sub_user in subaccount['users'].items():
                sub_identifiers = sub_user['identifiers']

                # Find matching identifiers
                matches = parent_identifiers & sub_identifiers

                if matches:
                    user_has_collision = True
                    users_with_collisions.add(parent_username)

                    # Determine collision type
                    for match in matches:
                        collision_type = []
                        if match == parent_username:
                            collision_type.append("parent_username")
                        if match in parent_user['aliases']:
                            collision_type.append("parent_alias")
                        if match == sub_username:
                            collision_type.append("sub_username")
                        if match in sub_user['aliases']:
                            collision_type.append("sub_alias")

                        collisions.append({
                            'parent_username': parent_username,
                            'parent_aliases': ', '.join(parent_user['aliases']) if parent_user['aliases'] else 'None',
                            'subaccount_name': account_name,
                            'subaccount_id': account_id,
                            'collision_type': ' & '.join(collision_type),
                            'matched_value': match,
                            'subaccount_username': sub_username
                        })

        if not user_has_collision:
            users_without_collisions.append({
                'parent_username': parent_username,
                'parent_aliases': ', '.join(parent_user['aliases']) if parent_user['aliases'] else 'None',
                'status': 'No collisions'
            })

    print(f"Collision detection complete!")
    print(f"  Users with collisions: {len(users_with_collisions)}")
    print(f"  Users without collisions: {len(users_without_collisions)}")
    print(f"  Total collision instances: {len(collisions)}")

    return collisions, users_without_collisions


def generate_csv_report(collisions, users_without_collisions, timestamp):
    """Generate CSV report of collisions."""
    filename = f"username_collision_report_{timestamp}.csv"

    # Combine collision data and no-collision data
    all_data = []

    # Add collisions
    for collision in collisions:
        all_data.append(collision)

    # Add users without collisions
    for user in users_without_collisions:
        all_data.append({
            'parent_username': user['parent_username'],
            'parent_aliases': user['parent_aliases'],
            'subaccount_name': 'N/A',
            'subaccount_id': 'N/A',
            'collision_type': 'No collision',
            'matched_value': 'N/A',
            'subaccount_username': 'N/A'
        })

    df = pd.DataFrame(all_data)
    df.to_csv(filename, index=False)
    print(f"\nCSV report saved to: {filename}")

    return filename


def generate_pdf_report(collisions, users_without_collisions, stats, timestamp):
    """Generate professional PDF report of collisions."""
    filename = f"username_collision_report_{timestamp}.pdf"

    doc = SimpleDocTemplate(filename, pagesize=letter,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=1*inch, bottomMargin=0.75*inch)

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12
    )

    # Build document
    story = []

    # Title
    title = Paragraph("Username Collision Report", title_style)
    story.append(title)
    story.append(Spacer(1, 0.2*inch))

    # Timestamp
    date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], alignment=TA_CENTER)
    date_text = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style)
    story.append(date_text)
    story.append(Spacer(1, 0.4*inch))

    # Summary Statistics
    story.append(Paragraph("Summary Statistics", heading_style))

    summary_data = [
        ['Metric', 'Count'],
        ['Total Parent Users', str(stats['total_parent_users'])],
        ['Users with Collisions', str(stats['users_with_collisions'])],
        ['Users without Collisions', str(stats['users_without_collisions'])],
        ['Total Collision Instances', str(stats['total_collisions'])],
        ['Subaccounts Scanned', str(stats['subaccounts_scanned'])]
    ]

    summary_table = Table(summary_data, colWidths=[3.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))

    # Collisions Detail
    if collisions:
        story.append(Paragraph("Collision Details", heading_style))
        story.append(Spacer(1, 0.1*inch))

        # Group collisions by parent username
        collisions_by_user = {}
        for collision in collisions:
            username = collision['parent_username']
            if username not in collisions_by_user:
                collisions_by_user[username] = []
            collisions_by_user[username].append(collision)

        for parent_username, user_collisions in collisions_by_user.items():
            # User header
            user_text = Paragraph(f"<b>Parent User:</b> {parent_username}", styles['Normal'])
            story.append(user_text)

            aliases = user_collisions[0]['parent_aliases']
            alias_text = Paragraph(f"<b>Aliases:</b> {aliases}", styles['Normal'])
            story.append(alias_text)
            story.append(Spacer(1, 0.1*inch))

            # Collision table for this user
            collision_data = [['Subaccount', 'Match Type', 'Matched Value']]
            for collision in user_collisions:
                collision_data.append([
                    collision['subaccount_name'],
                    collision['collision_type'],
                    collision['matched_value']
                ])

            collision_table = Table(collision_data, colWidths=[2.5*inch, 2*inch, 2*inch])
            collision_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ]))

            story.append(collision_table)
            story.append(Spacer(1, 0.2*inch))

    # Users without collisions
    if users_without_collisions:
        story.append(PageBreak())
        story.append(Paragraph("Users Without Collisions", heading_style))
        story.append(Spacer(1, 0.1*inch))

        no_collision_data = [['Parent Username', 'Aliases', 'Status']]
        for user in users_without_collisions[:50]:  # Limit to first 50 to avoid huge PDFs
            no_collision_data.append([
                user['parent_username'],
                user['parent_aliases'],
                user['status']
            ])

        if len(users_without_collisions) > 50:
            no_collision_data.append([
                f"... and {len(users_without_collisions) - 50} more",
                '',
                ''
            ])

        no_collision_table = Table(no_collision_data, colWidths=[2.5*inch, 2.5*inch, 1.5*inch])
        no_collision_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))

        story.append(no_collision_table)

    # Build PDF
    doc.build(story)
    print(f"PDF report saved to: {filename}")

    return filename


def main():
    print("Duo Security Username Collision Report")
    print("=" * 50)

    start_time = time.time()

    # Load configuration
    config = load_config()

    # Custom user agent for tracking
    custom_user_agent = "Delegated Access Uname Collision Report"

    # Initialize API clients
    parent_admin_client = duo_client.Admin(
        ikey=config['DUO_PARENT_IKEY'],
        skey=config['DUO_PARENT_SKEY'],
        host=config['DUO_PARENT_HOST'],
        user_agent=custom_user_agent
    )

    accounts_client = duo_client.Accounts(
        ikey=config['DUO_ACCOUNTS_IKEY'],
        skey=config['DUO_ACCOUNTS_SKEY'],
        host=config['DUO_ACCOUNTS_HOST'],
        user_agent=custom_user_agent
    )

    # Get parent users
    parent_users = get_parent_users(parent_admin_client)

    # Get subaccounts with users
    subaccounts_data = get_subaccounts_with_users(accounts_client, user_agent=custom_user_agent)

    # Detect collisions
    collisions, users_without_collisions = detect_collisions(parent_users, subaccounts_data)

    # Generate timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Prepare statistics
    stats = {
        'total_parent_users': len(parent_users),
        'users_with_collisions': len(parent_users) - len(users_without_collisions),
        'users_without_collisions': len(users_without_collisions),
        'total_collisions': len(collisions),
        'subaccounts_scanned': len(subaccounts_data)
    }

    # Print summary to console
    print("\n" + "=" * 50)
    print("COLLISION REPORT SUMMARY")
    print("=" * 50)
    summary_table = [
        ['Metric', 'Count'],
        ['Total Parent Users', stats['total_parent_users']],
        ['Users with Collisions', stats['users_with_collisions']],
        ['Users without Collisions', stats['users_without_collisions']],
        ['Total Collision Instances', stats['total_collisions']],
        ['Subaccounts Scanned', stats['subaccounts_scanned']]
    ]
    print(tabulate(summary_table, headers='firstrow', tablefmt='grid'))

    # Generate reports
    csv_file = generate_csv_report(collisions, users_without_collisions, timestamp)
    pdf_file = generate_pdf_report(collisions, users_without_collisions, stats, timestamp)

    # Print execution time
    execution_time = time.time() - start_time
    print(f"\nTotal execution time: {execution_time:.2f} seconds")
    print(f"\nReports generated:")
    print(f"  - CSV: {csv_file}")
    print(f"  - PDF: {pdf_file}")


if __name__ == "__main__":
    main()
