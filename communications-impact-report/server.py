#!/usr/bin/env python3
"""
Communications Impact Report - Flask proxy server

Handles POST /api/impact/<comm_id> requests from the browser UI.
Uses the Duo Accounts API to traverse child accounts and query each
for affected users/devices based on the specific communication.

Run with:
    pip install flask flask-cors
    python server.py
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import duo_client
import os
import re

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def parse_version(version_str):
    """Parse a version string into a tuple of ints for comparison."""
    if not version_str:
        return (0,)
    # Extract numeric parts only
    parts = re.findall(r'\d+', str(version_str))
    return tuple(int(p) for p in parts) if parts else (0,)


def get_child_accounts(ikey, skey, host):
    """Return list of child accounts using the Accounts API."""
    accounts_client = duo_client.Accounts(ikey=ikey, skey=skey, host=host)
    return accounts_client.get_child_accounts()


def make_admin_client(ikey, skey, host, account_id, child_hostname):
    """Create an AccountAdmin client for a child account.

    AccountAdmin automatically injects account_id into every API call,
    which is required when using Accounts API credentials against child accounts.
    """
    return duo_client.admin.AccountAdmin(
        account_id=account_id,
        child_api_host=child_hostname,
        ikey=ikey,
        skey=skey,
        host=host,
    )


# ---------------------------------------------------------------------------
# Impact handlers per comm_id
# ---------------------------------------------------------------------------

def impact_ios_android_eos(ikey, skey, host):
    """
    Duo Mobile End of Support: iOS 16 & Android 11

    Flags phones where:
      platform == "Apple iOS"  AND OS version <= 16
      platform == "Google Android" AND OS version <= 11
    """
    rows = []
    errors = []

    try:
        child_accounts = get_child_accounts(ikey, skey, host)
    except Exception as e:
        return None, f"Failed to retrieve child accounts: {e}"

    for acct in child_accounts:
        account_id = acct.get('account_id')
        account_name = acct.get('name', account_id or 'Unknown')
        api_hostname = acct.get('api_hostname')
        if not api_hostname or not account_id:
            errors.append(f"Missing account_id or api_hostname for account {account_name}, skipping.")
            continue

        try:
            admin_client = make_admin_client(ikey, skey, host, account_id, api_hostname)
            phones = admin_client.json_api_call('GET', '/admin/v1/phones', {})
        except Exception as e:
            errors.append(f"Error fetching phones for {account_name}: {e}")
            continue

        for phone in phones:
            platform = phone.get('platform', '')
            os_version_raw = phone.get('os_version') or phone.get('ios_version', '')
            version_tuple = parse_version(os_version_raw)

            affected = False
            if platform == 'Apple iOS' and version_tuple and version_tuple[0] <= 16:
                affected = True
            elif platform == 'Google Android' and version_tuple and version_tuple[0] <= 11:
                affected = True

            if affected:
                # Collect associated usernames
                users = phone.get('users', [])
                usernames = ', '.join(u.get('username', '') for u in users) if users else ''
                rows.append({
                    'account_name': account_name,
                    'username': usernames,
                    'platform': platform,
                    'os_version': os_version_raw or '',
                    'phone_number': phone.get('number', ''),
                })

    summary = {
        'total_affected': len(rows),
        'total_accounts_scanned': len(child_accounts),
        'total_affected_accounts': len({r['account_name'] for r in rows}),
        'errors': errors,
    }
    return {'summary': summary, 'rows': rows}, None


def impact_duo_desktop_update(ikey, skey, host):
    """
    Manually Update Duo Desktop Required

    Flags endpoints where OS is Windows and Duo Desktop version < 7.12.
    Uses GET /admin/v1/endpoints.
    """
    rows = []
    errors = []

    try:
        child_accounts = get_child_accounts(ikey, skey, host)
    except Exception as e:
        return None, f"Failed to retrieve child accounts: {e}"

    for acct in child_accounts:
        account_id = acct.get('account_id')
        account_name = acct.get('name', account_id or 'Unknown')
        api_hostname = acct.get('api_hostname')
        if not api_hostname or not account_id:
            errors.append(f"Missing account_id or api_hostname for account {account_name}, skipping.")
            continue

        try:
            admin_client = make_admin_client(ikey, skey, host, account_id, api_hostname)
            endpoints = admin_client.json_api_call('GET', '/admin/v1/endpoints', {})
        except Exception as e:
            errors.append(f"Error fetching endpoints for {account_name}: {e}")
            continue

        for ep in endpoints:
            os_name = ep.get('os', '') or ep.get('os_name', '')
            duo_desktop_ver = (
                ep.get('duo_desktop_version')
                or ep.get('security_agents', {}).get('duo_desktop', {}).get('version', '')
                if isinstance(ep.get('security_agents'), dict)
                else ''
            )

            if 'windows' not in os_name.lower():
                continue

            if not duo_desktop_ver:
                continue

            version_tuple = parse_version(duo_desktop_ver)
            # < 7.12 means tuple < (7, 12)
            if version_tuple < (7, 12):
                username = ep.get('username', ep.get('email', ''))
                rows.append({
                    'account_name': account_name,
                    'username': username,
                    'os': os_name,
                    'duo_desktop_version': duo_desktop_ver,
                })

    summary = {
        'total_affected': len(rows),
        'total_accounts_scanned': len(child_accounts),
        'total_affected_accounts': len({r['account_name'] for r in rows}),
        'errors': errors,
    }
    return {'summary': summary, 'rows': rows}, None


def impact_ca_bundle_expiration(ikey, skey, host):
    """
    MSPs: Upcoming CA Bundle Expiration

    Returns all rows from GET /admin/v1/unsupported_clients_log.
    """
    rows = []
    errors = []

    try:
        child_accounts = get_child_accounts(ikey, skey, host)
    except Exception as e:
        return None, f"Failed to retrieve child accounts: {e}"

    for acct in child_accounts:
        account_id = acct.get('account_id')
        account_name = acct.get('name', account_id or 'Unknown')
        api_hostname = acct.get('api_hostname')
        if not api_hostname or not account_id:
            errors.append(f"Missing account_id or api_hostname for account {account_name}, skipping.")
            continue

        try:
            admin_client = make_admin_client(ikey, skey, host, account_id, api_hostname)
            log_entries = admin_client.json_api_call('GET', '/admin/v1/unsupported_clients_log', {})
        except Exception as e:
            errors.append(f"Error fetching unsupported clients log for {account_name}: {e}")
            continue

        for entry in log_entries:
            rows.append({
                'account_name': account_name,
                'username': entry.get('username', ''),
                'client': entry.get('client', entry.get('user_agent', '')),
                'application': entry.get('application', entry.get('app_name', '')),
                'version': entry.get('version', entry.get('client_version', '')),
            })

    summary = {
        'total_affected': len(rows),
        'total_accounts_scanned': len(child_accounts),
        'total_affected_accounts': len({r['account_name'] for r in rows}),
        'errors': errors,
    }
    return {'summary': summary, 'rows': rows}, None


COMM_HANDLERS = {
    'ios_android_eos': impact_ios_android_eos,
    'duo_desktop_update': impact_duo_desktop_update,
    'ca_bundle_expiration': impact_ca_bundle_expiration,
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/api/impact/<comm_id>', methods=['POST'])
def get_impact(comm_id):
    if comm_id not in COMM_HANDLERS:
        return jsonify({'error': f"Unknown communication ID: {comm_id}"}), 404

    body = request.get_json(silent=True) or {}
    ikey = body.get('ikey', '').strip()
    skey = body.get('skey', '').strip()
    host = body.get('host', '').strip()

    if not ikey or not skey or not host:
        return jsonify({'error': 'Missing required credentials: ikey, skey, host'}), 400

    handler = COMM_HANDLERS[comm_id]
    result, error = handler(ikey, skey, host)

    if error:
        return jsonify({'error': error}), 500

    return jsonify(result)


@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    print("Communications Impact Report server starting on http://localhost:5000")
    print("Open http://localhost:5000 in your browser.")
    app.run(host='127.0.0.1', port=5000, debug=False)
