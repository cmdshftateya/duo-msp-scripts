#!/usr/bin/env python3
"""
Duo Security Phone OS Report

Generates a report of all enrolled phones across the parent account and all
subaccounts to help identify devices running end-of-life or end-of-support
operating systems.

Configuration:
    Reads from duo.conf:
    - DUO_PARENT_IKEY / DUO_PARENT_SKEY / DUO_PARENT_HOST
    - DUO_ACCOUNTS_IKEY / DUO_ACCOUNTS_SKEY / DUO_ACCOUNTS_HOST
"""

import html
import sys
import time
from datetime import datetime

import pandas as pd
from tabulate import tabulate

import duo_client


def load_config():
    config = {}
    try:
        with open('duo.conf', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    except FileNotFoundError:
        print("Error: duo.conf file not found.")
        sys.exit(1)

    required_keys = [
        'DUO_PARENT_IKEY', 'DUO_PARENT_SKEY', 'DUO_PARENT_HOST',
        'DUO_ACCOUNTS_IKEY', 'DUO_ACCOUNTS_SKEY', 'DUO_ACCOUNTS_HOST'
    ]
    missing = [k for k in required_keys if k not in config]
    if missing:
        print(f"Error: Missing required credentials in duo.conf: {', '.join(missing)}")
        sys.exit(1)

    return config


def get_account_name(admin_client):
    try:
        return admin_client.get_settings().get('name', 'Unknown Account')
    except Exception as e:
        print(f"  Warning: could not fetch account name: {e}")
        return 'Unknown Account'


def api_host_to_admin_host(api_hostname):
    """Convert api-xxxx.duosecurity.com to admin-xxxx.duosecurity.com"""
    return api_hostname.replace('api-', 'admin-', 1)


def build_admin_url(row, parent_admin_host):
    """
    Build a link to the Duo admin panel for a phone row.
    - Parent account: direct link to the phone detail page
    - Subaccount: reseller redirect into that account (drops on dashboard)
    """
    if not row['account_id']:
        # Parent account — link directly to phone
        phone_id = row['phone_id']
        return f"https://{parent_admin_host}/phones/{phone_id}" if phone_id else ''
    else:
        # Subaccount — reseller redirect, lands on dashboard
        return f"https://{parent_admin_host}/reseller?akey={row['account_id']}"


def get_phones_for_account(admin_client, account_name, account_id=None):
    params = {}
    if account_id:
        params['account_id'] = account_id

    try:
        phones = admin_client.json_api_call('GET', '/admin/v1/phones', params)
    except Exception as e:
        print(f"  Warning: could not fetch phones for {account_name}: {e}")
        return []

    rows = []
    for phone in phones:
        users = phone.get('users', [])
        usernames = [u.get('username', '') for u in users] if users else ['(no user)']

        for username in usernames:
            rows.append({
                'account': account_name,
                'account_id': account_id,
                'phone_id': phone.get('phone_id', ''),
                'username': username,
                'platform': phone.get('platform', 'Unknown'),
                'os_version': phone.get('os_version', ''),
                'model': phone.get('model', ''),
                'phone_number': phone.get('number', ''),
                'activated': phone.get('activated', False),
            })

    return rows


def export_html(df, summary, generated_at, html_filename):
    def e(val):
        return html.escape(str(val)) if val is not None else ''

    rows_html = ''
    for _, row in df.iterrows():
        url = row.get('admin_url', '')
        activated = '✓' if row['activated'] is True else ('✗' if row['activated'] is False else '')
        account_cell = (
            f'<a href="{e(url)}" target="_blank">{e(row["account"])}</a>'
            if url else e(row['account'])
        )
        rows_html += f"""
        <tr>
            <td>{account_cell}</td>
            <td>{e(row['username'])}</td>
            <td>{e(row['platform'])}</td>
            <td>{e(row['os_version'])}</td>
            <td>{e(row['model'])}</td>
            <td>{e(row['phone_number'])}</td>
            <td class="center">{activated}</td>
        </tr>"""

    summary_rows = ''
    for _, row in summary.iterrows():
        summary_rows += f"""
        <tr>
            <td>{e(row['platform'])}</td>
            <td>{e(row['os_version'])}</td>
            <td class="center">{e(row['count'])}</td>
        </tr>"""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Phones Report - All Accounts</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 13px;
    background: #f4f5f7;
    color: #1a1a2e;
    display: flex;
    min-height: 100vh;
  }}

  /* Sidebar */
  .sidebar {{
    width: 56px;
    background: #1b2a4a;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 16px;
    gap: 24px;
  }}
  .sidebar-logo {{
    width: 32px;
    height: 32px;
    background: #2d9cdb;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 800;
    font-size: 14px;
    letter-spacing: -1px;
  }}
  .sidebar-icon {{
    width: 28px;
    height: 28px;
    border-radius: 6px;
    background: rgba(255,255,255,0.07);
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(255,255,255,0.45);
    font-size: 14px;
    cursor: default;
  }}
  .sidebar-icon.active {{
    background: rgba(45,156,219,0.25);
    color: #2d9cdb;
  }}

  /* Main */
  .main {{
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}

  /* Top bar */
  .topbar {{
    background: #fff;
    border-bottom: 1px solid #e2e5ea;
    padding: 0 24px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }}
  .topbar-title {{
    font-size: 15px;
    font-weight: 600;
    color: #1b2a4a;
  }}
  .topbar-meta {{
    font-size: 11px;
    color: #8a93a2;
  }}

  /* Content */
  .content {{
    padding: 24px;
    overflow-y: auto;
    flex: 1;
  }}

  .section-title {{
    font-size: 12px;
    font-weight: 600;
    color: #8a93a2;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
    margin-top: 28px;
  }}
  .section-title:first-child {{
    margin-top: 0;
  }}

  /* Search bar */
  .search-bar {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 14px;
  }}
  .search-input {{
    width: 280px;
    padding: 6px 10px;
    border: 1px solid #d0d5dd;
    border-radius: 6px;
    font-size: 12px;
    color: #1a1a2e;
    outline: none;
    background: #fff;
  }}
  .search-input:focus {{
    border-color: #2d9cdb;
    box-shadow: 0 0 0 2px rgba(45,156,219,0.15);
  }}
  .result-count {{
    font-size: 12px;
    color: #8a93a2;
  }}

  /* Table */
  .table-wrap {{
    background: #fff;
    border: 1px solid #e2e5ea;
    border-radius: 8px;
    overflow: hidden;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
  }}
  thead th {{
    background: #f8f9fb;
    border-bottom: 1px solid #e2e5ea;
    padding: 9px 14px;
    text-align: left;
    font-size: 11px;
    font-weight: 600;
    color: #8a93a2;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    white-space: nowrap;
    cursor: pointer;
    user-select: none;
  }}
  thead th:hover {{ color: #1b2a4a; }}
  thead th .sort-arrow {{ margin-left: 4px; opacity: 0.4; }}
  thead th.sorted .sort-arrow {{ opacity: 1; color: #2d9cdb; }}

  tbody tr {{
    border-bottom: 1px solid #f0f2f5;
    transition: background 0.1s;
  }}
  tbody tr:last-child {{ border-bottom: none; }}
  tbody tr:hover {{ background: #f5f8ff; }}
  tbody td {{
    padding: 9px 14px;
    color: #2c3e50;
    font-size: 12.5px;
  }}
  tbody td a {{
    color: #2d9cdb;
    text-decoration: none;
    font-weight: 500;
  }}
  tbody td a:hover {{ text-decoration: underline; }}
  .center {{ text-align: center; }}

  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
  }}
  .badge-green {{ background: #e6f7ee; color: #1a7a45; }}
  .badge-gray  {{ background: #f0f2f5; color: #8a93a2; }}

  .hidden {{ display: none !important; }}
</style>
</head>
<body>

<div class="sidebar">
  <div class="sidebar-logo">D</div>
  <div class="sidebar-icon">⌂</div>
  <div class="sidebar-icon">👤</div>
  <div class="sidebar-icon active">📱</div>
  <div class="sidebar-icon">🔑</div>
  <div class="sidebar-icon">📊</div>
</div>

<div class="main">
  <div class="topbar">
    <span class="topbar-title">Phones Report - All Accounts</span>
    <span class="topbar-meta">Generated {e(generated_at)} &nbsp;·&nbsp; {len(df)} phones across {df['account'].nunique()} accounts</span>
  </div>

  <div class="content">

    <p class="section-title">All Phones</p>
    <div class="search-bar">
      <input class="search-input" id="phoneSearch" type="text" placeholder="Search by account, user, platform, OS…" oninput="filterTable()">
      <span class="result-count" id="phoneCount">{len(df)} results</span>
    </div>
    <div class="table-wrap">
      <table id="phoneTable">
        <thead>
          <tr>
            <th onclick="sortTable(0)">Account <span class="sort-arrow">↕</span></th>
            <th onclick="sortTable(1)">Username <span class="sort-arrow">↕</span></th>
            <th onclick="sortTable(2)">Platform <span class="sort-arrow">↕</span></th>
            <th onclick="sortTable(3)" class="sorted">OS Version <span class="sort-arrow">↑</span></th>
            <th onclick="sortTable(4)">Model <span class="sort-arrow">↕</span></th>
            <th onclick="sortTable(5)">Phone Number <span class="sort-arrow">↕</span></th>
            <th onclick="sortTable(6)" class="center">Activated <span class="sort-arrow">↕</span></th>
          </tr>
        </thead>
        <tbody id="phoneBody">
          {rows_html}
        </tbody>
      </table>
    </div>

    <p class="section-title">OS Version Summary</p>
    <div class="table-wrap" style="max-width: 480px;">
      <table>
        <thead>
          <tr>
            <th>Platform</th>
            <th>OS Version</th>
            <th class="center">Count</th>
          </tr>
        </thead>
        <tbody>
          {summary_rows}
        </tbody>
      </table>
    </div>

  </div>
</div>

<script>
  // --- Filter ---
  function filterTable() {{
    const q = document.getElementById('phoneSearch').value.toLowerCase();
    const rows = document.querySelectorAll('#phoneBody tr');
    let visible = 0;
    rows.forEach(row => {{
      const match = row.textContent.toLowerCase().includes(q);
      row.classList.toggle('hidden', !match);
      if (match) visible++;
    }});
    document.getElementById('phoneCount').textContent = visible + ' results';
  }}

  // --- Sort ---
  let sortCol = 3, sortAsc = true;
  function sortTable(col) {{
    const tbody = document.getElementById('phoneBody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    if (sortCol === col) {{ sortAsc = !sortAsc; }} else {{ sortAsc = true; sortCol = col; }}

    rows.sort((a, b) => {{
      const aVal = a.cells[col].textContent.trim();
      const bVal = b.cells[col].textContent.trim();
      // Version-aware sort for OS Version column
      if (col === 3) {{
        const aParts = aVal.split('.').map(Number);
        const bParts = bVal.split('.').map(Number);
        for (let i = 0; i < Math.max(aParts.length, bParts.length); i++) {{
          const diff = (aParts[i] || 0) - (bParts[i] || 0);
          if (diff !== 0) return sortAsc ? diff : -diff;
        }}
        return 0;
      }}
      return sortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }});

    // Empty values always last
    rows.sort((a, b) => {{
      const aEmpty = a.cells[col].textContent.trim() === '';
      const bEmpty = b.cells[col].textContent.trim() === '';
      if (aEmpty && !bEmpty) return 1;
      if (!aEmpty && bEmpty) return -1;
      return 0;
    }});

    rows.forEach(r => tbody.appendChild(r));

    // Update header arrows
    document.querySelectorAll('thead th').forEach((th, i) => {{
      th.classList.toggle('sorted', i === col);
      const arrow = th.querySelector('.sort-arrow');
      if (arrow) arrow.textContent = i === col ? (sortAsc ? '↑' : '↓') : '↕';
    }});
  }}
</script>
</body>
</html>"""

    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)


def get_subaccounts(accounts_client):
    try:
        return accounts_client.get_child_accounts()
    except Exception as e:
        print(f"Error getting subaccounts: {e}")
        return []


def main():
    print("Duo Security Phone OS Report")
    print("=============================")

    start_time = time.time()
    config = load_config()

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

    all_rows = []
    parent_admin_host = api_host_to_admin_host(config['DUO_PARENT_HOST'])

    # Parent account
    parent_name = get_account_name(parent_admin_client)
    print(f"\nProcessing parent account: {parent_name}")
    rows = get_phones_for_account(parent_admin_client, parent_name)
    print(f"  {len(rows)} phone(s)")
    all_rows.extend(rows)

    # Subaccounts
    subaccounts = get_subaccounts(accounts_client)
    print(f"\nFound {len(subaccounts)} subaccounts")

    for sub in subaccounts:
        account_id = sub['account_id']
        account_name = sub['name']
        api_hostname = sub['api_hostname']

        print(f"Processing: {account_name} ({account_id})")

        sub_admin_client = duo_client.Admin(
            ikey=accounts_client.ikey,
            skey=accounts_client.skey,
            host=api_hostname
        )

        rows = get_phones_for_account(sub_admin_client, account_name, account_id=account_id)
        print(f"  {len(rows)} phone(s)")
        all_rows.extend(rows)

    if not all_rows:
        print("\nNo phones found across any account.")
        return

    df = pd.DataFrame(all_rows)

    # Build admin panel URLs
    df['admin_url'] = df.apply(lambda row: build_admin_url(row, parent_admin_host), axis=1)

    # Sort by os_version ascending (empty strings sort last)
    df['_os_sort'] = df['os_version'].replace('', None)
    df = df.sort_values('_os_sort', ascending=True, na_position='last').drop(columns='_os_sort')

    # Console display (drop internal columns)
    display_cols = ['account', 'username', 'platform', 'os_version', 'model', 'phone_number', 'activated']
    print("\n\nPhone OS Report Across All Accounts:")
    print(tabulate(df[display_cols], headers='keys', tablefmt='grid', showindex=False))

    # Summary: device count per platform + os_version
    print("\n\nOS Version Summary:")
    summary = (
        df.groupby(['platform', 'os_version'], dropna=False)
        .size()
        .reset_index(name='count')
        .sort_values(['platform', 'os_version'])
    )
    print(tabulate(summary, headers='keys', tablefmt='grid', showindex=False))

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    generated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    csv_filename = f"duo_phone_os_report_{timestamp}.csv"
    df[display_cols].to_csv(csv_filename, index=False)
    print(f"\nCSV saved to:  {csv_filename}")

    html_filename = f"duo_phone_os_report_{timestamp}.html"
    export_html(df, summary, generated_at, html_filename)
    print(f"HTML saved to: {html_filename}")

    total_time = time.time() - start_time
    print(f"Total phones: {len(all_rows)} | Accounts: {1 + len(subaccounts)} | Time: {total_time:.2f}s")


if __name__ == "__main__":
    main()
