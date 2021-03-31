import asyncio
import random
from datetime import datetime

import requests
from config import DOMAIN, GITHUB_APP_NAME
from install import install_and_uninstall_if_necessary
from login import setup_login
from organization import organizations_to_install_on

if __name__ == '__main__':
    session = requests.Session()

    # Handle logging in
    print(datetime.now())
    print(f'GitHub App: {GITHUB_APP_NAME}, Domain: {DOMAIN}')
    print('\n')
    setup_login(session=session)

    # Get all organizations
    for organization_tuple in organizations_to_install_on(session):
        # Handle installation for one organization
        target_name, target_install_url = organization_tuple
        print(f'Found organization/user: {target_name}, to install app: {GITHUB_APP_NAME}.')

        install_and_uninstall_if_necessary(
            session=session, target_name=target_name, target_install_url=target_install_url
        )

        # Sleep briefly between installations
        delay = random.randint(5, 20)
        asyncio.run(asyncio.sleep(delay))
        print('\n')
    print('\n')
