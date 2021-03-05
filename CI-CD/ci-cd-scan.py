#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
import os
import requests
import sys
import subprocess

from http import HTTPStatus
from time import sleep
from typing import List


def init_logger():
    logger = logging.getLogger('CI/CD Scan')
    logger.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    logger.addHandler(h)

    return logger


def get_base_branch():
    remote_branches = subprocess.run(['git', 'branch', '-r'], check=True,
                                     stdout=subprocess.PIPE).stdout.decode('utf-8', errors='replace').split()
    if 'origin/main' in (branch.strip() for branch in remote_branches):
        return 'origin/main'
    return 'origin/master'


logger = init_logger()


class Scan:
    """
    Scan represents an CI/CD scan BluBracket service is running
    """

    def __init__(self, client: CiCdScanClient, scan_uuid: str):
        """
        Args:
            client: CI/CD scan client used to request the scan
            scan_uuid: The scan_uuid returned from the CiCdScanClient when creating the scan
        """

        self.client = client
        self.api = client.api + "/" + scan_uuid

    def get_result(self, retries: int = 20) -> dict:
        """
        Poll for CI/CD scan result `retries` times.
        If the result is not available after polling `retries` times, return None.

        Args:
            retries: the number of times to poll

        Returns:
            A dictionary representing the scan result.
            Format:
                {
                    "secrets": {
                        "<commit_hash>": {
                            "secret_hash": "<secret_hash>",
                            "secret_type": "<secret_type>",
                            "file_path": "<file_path">,
                            "line_no": <line_no>,
                            "cols": [<col1>, <col2>]
                        }
                    }
                }
        """

        ready = False
        for retry in range(retries):
            if retry > 0:
                sleep(10)

            try:
                resp = client.get(self.api)
            except Exception as e:
                if retry == retries - 1:
                    raise e

                logger.info(
                    f'Failed to make a request to get the result: {e}. Retrying...')
                continue

            if resp.status_code == HTTPStatus.OK:
                ready = True
                break
            elif resp.status_code in (HTTPStatus.BAD_GATEWAY, HTTPStatus.SERVICE_UNAVAILABLE, HTTPStatus.GATEWAY_TIMEOUT):
                logger.info(f'Service error. HTTP Status: {resp.status_code}')
            elif resp.status_code != HTTPStatus.ACCEPTED:
                if resp.status_code in (HTTPStatus.BAD_REQUEST, HTTPStatus.INTERNAL_SERVER_ERROR):
                    try:
                        err_msg = resp.json().get('message')
                    except Exception as e:
                        err_msg = f'Unable to get the error message in the response: {e}'
                else:
                    err_msg = f'Service error. HTTP Status: {resp.status_code}'
                raise Exception(f'Failed to get the result: {err_msg}')

            logger.info(
                f'Polled {retry+1} times. The result is not ready yet.')

        if not ready:
            logger.error(f'Unable to get the result after {retries} polls')
            return None

        logger.info('The result is now ready')
        return resp.json()


class CicdScanClient:
    """
    The client to make requests to BluBracket CI/CD scan service.
    """

    def __init__(self, api: str, token: str):
        """
        Args:
             api: Normally the API is https://<tenant-name>.blubracket.com/api/analyzer/commit/scan
             token: BluBracket CI/CD token
        """

        self.token = token
        self.auth_header = {'Authorization': 'Bearer ' + token}
        self.api = api

    def scan_pull_request(self, repo_url: str, pull_request_number: int) -> Scan:
        """
        Request BluBracket CI/CD scan service to scan a pull request

        Args:
            repo_url: the URL to the repository. The URL can start with either git:// or https://
            pull_request_number: The identification number of the pull request

        Returns:
            A Scan object representing the created CI/CD scan
        """

        body = {
            'repo_url': repo_url,
            'pull_request_number': pull_request_number,
        }

        return self._scan(body)

    def scan_commits(self, repo_url: str, commits: List[str]) -> Scan:
        """
        Request BluBracket CI/CD scan service to scan a list of commits

        Args:
            repo_url: the URL to the repository. The URL can start with either git:// or https://
            commits: A list of hashes of the commits

        Returns:
            A Scan object representing the created CI/CD scan
        """

        body = {
            'repo_url': repo_url,
            'commit_shas': commits,
        }

        return self._scan(body)

    def post(self, api, *args, **kwargs):
        return requests.post(api, headers=self.auth_header, *args, **kwargs)

    def get(self, api, *args, **kwargs):
        return requests.get(api, headers=self.auth_header, *args, **kwargs)

    def _scan(self, body: dict) -> Scan:
        try:
            resp = self.post(self.api, json=body)
        except Exception as e:
            raise Exception(f'Failed to start the scan when posting: {e}')

        if resp.status_code != HTTPStatus.OK:
            try:
                err_msg = resp.json().get('message')
            except Exception as e:
                err_msg = str(e)

            raise Exception(f'Failed to start the scan: {err_msg}')

        return Scan(client=self, scan_uuid=resp.json()['scan_uuid'])


if __name__ == '__main__':
    # Normally the URL is https://<tenant-name>.blubracket.com/api/analyzer/commit/scan
    ci_cd_api = os.getenv('BLUBRACKET_CI_CD_API')
    if ci_cd_api is None:
        logger.error('No CI/CD api endpoint specified')

    ci_cd_token = os.getenv('BLUBRACKET_CI_CD_TOKEN')
    if ci_cd_token is None:
        logger.error('No CI/CD api token specified')

    # BUILD_REPOSITORY_URI can start with either git:// or https://
    repo_url = os.getenv('BUILD_REPOSITORY_URI')
    if repo_url is None:
        logger.error('No repository url specified')

    # Azure pipeline set the `SYSTEM_PULLREQUEST_PULLREQUESTNUMBER` env variable when the build
    # is caused by a pull request.
    # See https://docs.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops&tabs=yaml#system-variables-devops-services
    pull_request_number = os.getenv('SYSTEM_PULLREQUEST_PULLREQUESTNUMBER')
    if pull_request_number is None:
        # If the build is not caused by a pull request but a branch `b`,
        # scan the branch `b` from the tip of the `b` to the common ancestor of `b` and `master`.
        # That is, we assume the branch is to be merged in to the `master` branch.
        base_branch = get_base_branch()
        base_commit = subprocess.run(['git', 'merge-base', base_branch, 'HEAD'], check=True,
                                     stdout=subprocess.PIPE).stdout.decode('utf-8', errors='replace').strip()
        commits = subprocess.run(['git', 'rev-list', f'{base_commit}..HEAD'], check=True,
                                 stdout=subprocess.PIPE).stdout.decode('utf-8', errors='replace').strip().split()
        if not commits:
            logger.info("No pull request number and commits specified")

    if None in (ci_cd_api, ci_cd_token, repo_url):
        # API, token and the url of the repository are required
        exit(1)

    if pull_request_number is None and not commits:
        # Exit immediately if no pull request number or commits to scan
        exit(0)

    try:
        logger.info(f'BLUBRACKET_CI_CD_API: {ci_cd_api}')
        logger.info(f'BUILD_REPOSITORY_URI: {repo_url}')
        logger.info(f'BLUBRACKET_CI_CD_TOKEN: ******')
        client = CicdScanClient(ci_cd_api, ci_cd_token)
        if pull_request_number is not None:
            logger.info(
                f'Requesting to scan pull request #{pull_request_number}')
            scan = client.scan_pull_request(repo_url, int(pull_request_number))
        else:
            logger.info(f'Requesting to scan commits {commits}')
            scan = client.scan_commits(repo_url, commits)
        result = scan.get_result()
        if not result:
            print(
                '##vso[task.complete result=SucceededWithIssues;] Unable to get the result from the scan API')
            exit(0)

        if result['secrets']:
            print('Secrets found in commits:')
            print('\n'.join(result['secrets'].keys()))
            print()
            print('Scan result:')
            print(json.dumps(result, indent=4))
            # Currently we don't fail the build if secrets are found.
            # Instead we mark the stage as "partially succeeded" and a warning icon is shown on the build.
            # See https://docs.microsoft.com/en-us/azure/devops/pipelines/scripts/logger-commands?view=azure-devops&tabs=bash#complete-finish-timeline
            print(
                '##vso[task.complete result=SucceededWithIssues;] Secrets found')
        else:
            print('No secrets found')
    except Exception as e:
        logger.error(f'Failed to run the CI/CD scan: {e}')
        exit(1)
