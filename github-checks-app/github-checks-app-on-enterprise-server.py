import logging
import sys
from secrets import token_urlsafe
from urllib.parse import urlencode, urlparse


def init_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    logger.addHandler(h)

    return logger


logger = init_logger()


if __name__ == '__main__':
    domain = input('Enter your GitHub Enterprise Server domain name (i.e. github.companyname.com): ')

    domain = urlparse(domain if '//' in domain else f'//{domain}').netloc

    query_params = {
        'name': 'HashiCorp Vault Radar App',
        'webhook_secret': token_urlsafe(nbytes=32),
        'webhook_url': f'https://api.hashicorp.cloud/2023-05-01/vault-radar/api/github-apps/events?domain={domain}',
        'public': True,
        'webhook_active': True,
        'url': 'https://www.hashicorp.com/',
        'checks': 'write',
        'events[]': ['check_run', 'check_suite', 'pull_request'],
        'pull_requests': 'read',
    }
    query_param_string = urlencode(query_params, doseq=True, safe=':/?=[]')
    
    url = f'https://{domain}/settings/apps/new?{query_param_string}'
    logger.info(url)
