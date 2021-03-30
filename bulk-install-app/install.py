from config import DOMAIN, GITHUB_APP_NAME
from debug import save
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import re


def start_install(session, target_name, target_id):
    """
    Start the installation process by pulling the install and authorize form.
    Returns tuple of (authenticity_token, target_type, integration_fingerprint).

    Will return None if current user does not have permissions to install.
    """
    url = f'https://{DOMAIN}/apps/{GITHUB_APP_NAME}/installations/new/permissions?target_id={target_id}'
    installation_response = session.get(url)
    installation_page_soup = BeautifulSoup(installation_response.content, 'html.parser')
    save(folder='install-data', name='install', response=installation_response)

    installation_button = installation_page_soup.find('button', {'data-octo-click': 'install_integration'})
    if 'install & authorize' in installation_button.string.lower():
        print(f'User has permissions to install on organization/user: {target_name}. Installing.')
    elif 'authorize & request' in installation_button.string.lower():
        print(f'User does not have permissions to install on organization/user: {target_name}. Skipping. ')
        return
    else:
        print(f'Error parsing installation page and button for organization/user: {target_name}. Skipping. ')
        return

    installation_form = installation_page_soup.find('form', {'action': f'/apps/{GITHUB_APP_NAME}/installations'})
    authenticity_token = installation_form.find('input', {'name': 'authenticity_token'}).get('value')
    target_type = installation_form.find('input', {'name': 'target_type'}).get('value')
    integration_fingerprint = installation_form.find('input', {'name': 'integration_fingerprint'}).get('value')

    return authenticity_token, target_type, integration_fingerprint


def process_install(session, authenticity_token, target_id, target_type, integration_fingerprint):
    """
    Install the app on the target_id / target_type specified in input params.
    """
    url = f'https://{DOMAIN}/apps/{GITHUB_APP_NAME}/installations'
    installation_request_data = {
        'authenticity_token': authenticity_token,
        'target_id': target_id,
        'target_type': target_type,
        'version_id': '147771',
        'integration_fingerprint': integration_fingerprint,
        'install_target': 'all',
    }

    headers = {
        'authority': f'{DOMAIN}',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'upgrade-insecure-requests': '1',
        'origin': f'https://{DOMAIN}',
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'referer': f'https://{DOMAIN}/apps/{GITHUB_APP_NAME}/installations/new/permissions?target_id={target_id}',
        'accept-language': 'en-US,en;q=0.9',
    }

    installed_response = session.post(url, installation_request_data, headers=headers)
    installed_page_soup = BeautifulSoup(installed_response.content, 'html.parser')
    save(folder='install-data', name='installed', response=installed_response)

    return installed_page_soup


def redirect_install(session, installed_page_soup) -> bool:
    """
    Handle the redirect to the app's callback URL.
    Returns a boolean for whether the installation succeeded.
    """
    redirect_element = installed_page_soup.find('a', {'id': 'redirect'})
    if not redirect_element:
        return False

    redirect_url = redirect_element.get('href')
    if not redirect_url:
        return False

    redirect_response = session.get(redirect_url)
    save(folder='install-data', name='redirect', response=redirect_response)
    return 'success' in redirect_response.text.lower()


def install(session, target_name, target_id):
    """
    Manages full installation workflow - start, process, redirect.
    Returns boolean for whether this has occurred without any errors.
    """
    try:
        installation_data = start_install(session=session, target_name=target_name, target_id=target_id)
        if installation_data:
            authenticity_token, target_type, integration_fingerprint = installation_data
            installed_page_soup = process_install(
                session=session,
                authenticity_token=authenticity_token,
                target_id=target_id,
                target_type=target_type,
                integration_fingerprint=integration_fingerprint
            )

            success = redirect_install(session=session, installed_page_soup=installed_page_soup)
            if success:
                print(f'Succeeded installation for GitHub organization/user: {target_name}')
            else:
                print(f'Failed installation for GitHub organization/user: {target_name}')
            return success
        return True
    except Exception:
        return False


def check_uninstall(uninstall_complete_page):
    """
    Given the resulting uninstall page, check to see if uninstall succeeded.
    """
    uninstall_complete_page_message = uninstall_complete_page.find(
        'div', {'class': re.compile('container-lg*', re.IGNORECASE)}
    )
    return 'job has been queued to uninstall' in uninstall_complete_page_message.text


def uninstall(session, target_name, target_id):
    """
    Manages full uninstallation workflow - start, complete.
    Returns boolean for whether uninstall succeeded.
    """
    try:
        url = f'https://{DOMAIN}/apps/{GITHUB_APP_NAME}/installations/new/permissions?target_id={target_id}'
        uninstall_start_response = session.get(url)
        save(folder='uninstall-data', name=f'uninstall-{target_name}-start', response=uninstall_start_response)

        uninstallation_page_soup = BeautifulSoup(uninstall_start_response.content, 'html.parser')
        uninstallation_form = uninstallation_page_soup.find('form', {'action': re.compile('/settings/installations/[0-9]*$')})

        authenticity_token = uninstallation_form.find('input', {'name': 'authenticity_token'}).get('value')
        uninstallation_action = uninstallation_form.get('action')

        uninstall_data = {'authenticity_token': authenticity_token, '_method': 'delete'}
        uninstall_complete_response = session.post(f'https://{DOMAIN}{uninstallation_action}', uninstall_data)
        save(folder='uninstall-data', name=f'uninstall-{target_name}-complete', response=uninstall_complete_response)
        uninstall_complete_page = BeautifulSoup(uninstall_complete_response.content, 'html.parser')
        return check_uninstall(uninstall_complete_page)
    except Exception:
        return False


def install_and_uninstall_if_necessary(session, target_name, target_install_url):
    """
    Attempts to install the app on the organization/user. Filters out organization/user if logged in user does not
    have the correct permissions.
    """
    target_id = parse_qs(urlparse(target_install_url).query)['target_id'][0]
    installation_without_errors = install(session=session, target_name=target_name, target_id=target_id)
    if not installation_without_errors:
        uninstall_success = uninstall(session=session, target_name=target_name, target_id=target_id)

        if not uninstall_success:
            print(
                f'ERROR: Installation and uninstallation failed for GitHub organization/user: {target_name}. '
                f'Double check that org/user has been imported in BluBracket portal. Then, '
                f'manually uninstall and re-install this app for this organization/user. If failure continues, '
                f'contact support. '
            )
        else:
            print(
                f'WARNING: Installation failed for GitHub organization/user: {target_name}. Uninstall succeeded. '
                f'Double check that org/user has been imported in BluBracket portal, and re-run this script. '
                f'If failure continues, contact support. '
            )
