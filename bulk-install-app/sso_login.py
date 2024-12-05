import re
import traceback
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from config import DOMAIN, PASSWORD, USERNAME
from debug import save_debug_info


def pre_login(session):
    """Handle any redirects and retrieve the actual login url"""
    target_url = session.get(f'https://{DOMAIN}/login').url
    return target_url


def start_login(session, target_url):
    """
    Start the login process by pulling the login form.
    """
    login_response = session.get(target_url)
    login_page_soup = BeautifulSoup(login_response.content, 'html.parser')
    save_debug_info(folder='sso-login-data', name='login-start', response=login_response)

    login_form = login_page_soup.find('form', {'method': 'POST', 'action': re.compile('/idp/*')})
    return login_form


def complete_login(session, target_url, login_form):
    """
    Complete the login process by pulling the authenticity token from the login form,
    and sending username/password.
    """
    login_request_data = {
        'pf.username': USERNAME,
        'pf.pass': PASSWORD,
        'pf.ok': 'clicked',
        'pf.cancel': '',
        'pf.adapterId': 'HTMLLoginFormAdapter',
    }

    target_url_base = urlparse(target_url).netloc
    target_url_path = login_form.get('action')

    login_response = session.post(f'https://{target_url_base}{target_url_path}', login_request_data)
    login_page_soup = BeautifulSoup(login_response.content, 'html.parser')
    save_debug_info(folder='sso-login-data', name='login-complete', response=login_response)

    return login_page_soup


def check_login_success(login_page_soup):
    """
    Given the resulting login page, check to see if login succeeded.
    """
    return 'didn\'t recognize the username or password' not in login_page_soup.get_text()


def check_tfa_success(tfa_login_page):
    """
    Given the resulting two-factor login page, check to see if two-factor succeeded.
    """
    tfa_login_page_auth = tfa_login_page.find('div', {'class': re.compile('auth-form-header*', re.IGNORECASE)})
    if not tfa_login_page_auth:
        return True

    tfa_login_page_header = tfa_login_page_auth.find('h1')
    return 'two-factor' not in tfa_login_page_header.string.lower()


def handle_tfa(session, login_page_soup):
    """
    Check if two factor is necessary, and handle if necessary.
    Return boolean for whether two-factor step has succeeded (should return True if two-factor is unnecessary).
    """
    tfa_unnecessary = check_tfa_success(tfa_login_page=login_page_soup)
    if tfa_unnecessary:
        print('Two-factor authentication not required.')
        return True

    otp = input('Two-factor authentication required, input here: ')

    two_factor_form = login_page_soup.find('form', {'action': {'/sessions/two-factor'}})
    authenticity_token = two_factor_form.find('input', {'name': 'authenticity_token'}).get('value')
    two_factor_data = {'authenticity_token': authenticity_token, 'otp': otp}
    tfa_response = session.post('https://github.com/sessions/two-factor', two_factor_data)
    save_debug_info(folder='sso-login-data', name='tfa', response=tfa_response)

    tfa_login_page = BeautifulSoup(tfa_response.content, 'html.parser')

    return check_tfa_success(tfa_login_page=tfa_login_page)


def setup_login(session):
    try:
        target_url = pre_login(session)
        login_form = start_login(session=session, target_url=target_url)

        login_page_soup = complete_login(session=session, target_url=target_url, login_form=login_form)

        login_success = check_login_success(login_page_soup=login_page_soup)
        login_success = login_success and handle_tfa(session=session, login_page_soup=login_page_soup)
    except Exception:
        traceback.print_exc()
        login_success = False

    if login_success:
        print(f'Succeeded to login for GitHub SSO user: {USERNAME} \n')
        return
    print(f'Failed to login for GitHub SSO user: {USERNAME} \n')
