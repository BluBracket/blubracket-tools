import asyncio
import random
from datetime import datetime

import requests
from config import DOMAIN, GITHUB_APP_NAME, MAX_ORGANIZATIONS
from install import install_and_uninstall_if_necessary
from login import setup_login
from organization import organizations_to_install_on

if __name__ == '__main__':
    session = requests.Session()

    # Handle logging in
    print(datetime.now())
    print(f'GitHub App: {GITHUB_APP_NAME}, Domain: {DOMAIN}, Max Organizations: {MAX_ORGANIZATIONS}')
    print('\n')
    setup_login(session=session)

    # Get all organizations
    successful_installation_counter = 0
    for organization_tuple in organizations_to_install_on(session):
        # Handle installation for one organization
        target_name, target_install_url = organization_tuple
        print(f'Found organization/user: {target_name}, to install app: {GITHUB_APP_NAME}.')

        installation_success = install_and_uninstall_if_necessary(
            session=session, target_name=target_name, target_install_url=target_install_url
        )

        print('\n')

        # Stop early if succeeded on max installations
        successful_installation_counter += int(installation_success)
        if MAX_ORGANIZATIONS and successful_installation_counter == MAX_ORGANIZATIONS:
            print(f'Hit max organizations: {MAX_ORGANIZATIONS}, finishing. ')
            break

        # Sleep briefly between installations
        delay = random.randint(5, 20)
        asyncio.run(asyncio.sleep(delay))
    print('\n')
