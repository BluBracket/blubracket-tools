import re

from bs4 import BeautifulSoup
from config import DOMAIN, GITHUB_APP_NAME
from debug import save


def organizations_by_page(session):
    """
    Returns a generator of organizations/users to install the app on, by page.
    """
    url = f'https://{DOMAIN}/apps/{GITHUB_APP_NAME}/installations/new'
    app_install_response = session.get(url)
    save(folder='organization-data', name='page-1', response=app_install_response)
    app_install_page_soup = BeautifulSoup(app_install_response.content, 'html.parser')
    app_install_page_main = app_install_page_soup.find('div', {'class': 'application-main'})
    current_elem = app_install_page_soup.find('em', {'class': 'current'})
    yield app_install_page_main

    if current_elem:
        total_pages = current_elem.get('data-total-pages')
        for page_number in range(2, int(total_pages) + 1):
            app_install_response = session.get(f'{url}?page={page_number}')
            save(folder='organization-data', name=f'page-{page_number}', response=app_install_response)
            app_install_page_soup = BeautifulSoup(app_install_response.content, 'html.parser')
            app_install_page_main = app_install_page_soup.find('div', {'class': 'application-main'})
            yield app_install_page_main


def organizations_by_item(app_install_page_soup):
    """
    Given a page of organizations/users to install the app on, returns a generator by item.
    Filters out organizations/users that have already installed the app.
    """
    for row in app_install_page_soup.find_all('a', {'class': re.compile('Box-row*', re.IGNORECASE)}):
        target_name = row.find('img').get('alt').lstrip('@')
        target_install_url = row.get('href')
        if 'is installed' in row.find('span').get('aria-label').lower():
            print(f'Organization/user: {target_name} has already installed app: {GITHUB_APP_NAME}. Skipping. \n')
            continue
        yield target_name, target_install_url


def organizations_to_install_on(session):
    """
    Returns a generator of organizations to install on.
    """
    for app_install_page_soup in organizations_by_page(session=session):
        for organization_tuple in organizations_by_item(app_install_page_soup=app_install_page_soup):
            yield organization_tuple
