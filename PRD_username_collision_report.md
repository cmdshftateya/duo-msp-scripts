# Product Requirements Document: Username Collision Report

## Overview
Create a script that identifies username and alias collisions between a Duo parent account and all its subaccounts. The script will detect when usernames or aliases from the parent account exist in any subaccount, generating a comprehensive collision report.

## Objectives
- Identify username/alias collisions across parent and subaccounts
- Generate clear, actionable reports showing which subaccounts have collisions
- Provide visibility into potential user conflicts before account operations

## Technical Requirements

### API Integration
1. **Parent Admin API**
   - Authenticate using parent admin credentials (DUO_PARENT_IKEY, DUO_PARENT_SKEY, DUO_PARENT_HOST)
   - Retrieve all users from parent account
   - Extract usernames and aliases for each user

2. **Accounts API + Subaccount Admin API**
   - Authenticate using accounts API credentials (DUO_ACCOUNTS_IKEY, DUO_ACCOUNTS_SKEY, DUO_ACCOUNTS_HOST)
   - Retrieve list of all child/subaccounts
   - For each subaccount, create Admin API client using subaccount's api_hostname
   - Retrieve all users from each subaccount
   - Extract usernames and aliases for each subaccount user

### Data Collection
1. **Parent Account User Data**
   - Username (primary identifier)
   - Aliases (array of alternative usernames)
   - User ID (for reference)

2. **Subaccount User Data**
   - For each subaccount:
     - Account ID
     - Account name
     - Usernames and aliases of all users in that subaccount

### Collision Detection Logic
For each user in the parent account:
1. Create a set containing the username and all aliases
2. For each subaccount:
   - Check if any parent username/alias matches any subaccount username
   - Check if any parent username/alias matches any subaccount alias
3. Record matches as collisions

### Report Structure
The report should include:
1. **Per-User Collision Report**
   - Parent username
   - Parent aliases
   - List of subaccounts with collisions
   - For each collision:
     - Subaccount name
     - Subaccount ID
     - Specific matching username/alias
     - Type of match (username-to-username, username-to-alias, alias-to-username, alias-to-alias)

2. **Summary Statistics**
   - Total parent users checked
   - Number of parent users with collisions
   - Number of parent users with no collisions
   - Total subaccounts scanned
   - Subaccounts with most collisions

### Output Format
- **Console output**: Formatted table showing collision summary
- **CSV file**: Detailed collision report with timestamp in filename
  - Format: `username_collision_report_YYYYMMDD_HHMMSS.csv`
  - Columns: parent_username, parent_aliases, subaccount_name, subaccount_id, collision_type, matched_value
- **PDF file**: Professional formatted PDF report with timestamp in filename
  - Format: `username_collision_report_YYYYMMDD_HHMMSS.pdf`
  - Include summary statistics at top
  - Formatted tables with collision details
  - Visual separation between users
  - Professional styling with headers/footers

### Error Handling
- Handle API authentication failures gracefully
- Handle rate limiting with appropriate delays
- Continue processing if individual subaccount fails
- Log errors without stopping entire report generation

### Performance Considerations
- Track timing for each subaccount
- Report total execution time
- Consider pagination for large user sets
- Optimize by building lookup dictionaries for subaccount users

## Configuration
- Use existing duo.conf pattern for credentials
- Required credentials:
  - DUO_PARENT_IKEY
  - DUO_PARENT_SKEY
  - DUO_PARENT_HOST
  - DUO_ACCOUNTS_IKEY
  - DUO_ACCOUNTS_SKEY
  - DUO_ACCOUNTS_HOST

## Dependencies
- duo_client library
- pandas (for data handling)
- tabulate (for console output)
- reportlab (for PDF generation)
- Standard library: os, sys, datetime, time

## Success Criteria
1. Script successfully retrieves users from parent account
2. Script successfully retrieves users from all subaccounts
3. Collision detection accurately identifies all username/alias matches
4. Report clearly shows which subaccounts have collisions for each parent user
5. Report shows "no collisions" for parent users without matches
6. CSV export contains complete, accurate collision data
7. PDF export contains formatted, professional collision report
8. Script handles errors without crashing

## Future Enhancements (Out of Scope)
- Reverse collision check (subaccount to parent)
- Cross-subaccount collision detection
- Interactive collision resolution
- Email notification of collisions
- Remediation suggestions
