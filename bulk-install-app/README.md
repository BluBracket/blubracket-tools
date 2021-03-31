# [BluBracket](https://blubracket.com/) Bulk Installation Script for GitHub Checks App

## Bulk installing a GitHub Checks App across organizations
1. Navigate to BluBracket portal, and import the organizations that need to install the GitHub App 
2. In `blubracket-tools/bulk-install-app/`, generate an environment file `.env`, with the following variables set:
   - `BLU_USERNAME` - the GitHub user's username
   - `BLU_PASSWORD` - the GitHub user's password
   - `BLU_DOMAIN` - the domain of the GitHub Enterprise Server (optional: only required for GitHub Enterprise Server)
3. Run the script with the following command: `python3 -u main.py | tee -a bulk-install-app-results.txt`  
   NOTE: Only organizations/users that the logged in GitHub user has permissions to install on will be installed.
   - If two-factor authentication is enabled, the script with request input for the one-time password.
4. Take note of instances of the following logs, which require action:
   - ```User does not have permissions to install on organization/user: <organization_name>. Skipping. ```
      - Action item: Give install permissions to the logged-in user, or log-in with another user who has install permissions on <organization_name>. Re-run the script. 
   - ```Failed installation for GitHub organization/user: <organization_name>. WARNING: ...```
      - Action item: Double check that the organization is imported in the BluBracket portal (from step 1.), and re-run the script. If failure continues, contact support.
   - ```Failed installation for GitHub organization/user: <organization_name>. ERROR: ...```
      - Action item: Manually uninstall the app from the organization, double check that the organization is imported in the BluBracket portal (from step 1.), then manually install the app on this organization or re-run the script. If failure continues, contact support.
        
When contacting support, please send over the `bulk-install-app-results.txt` file generated from step 3. 
   
   
   


