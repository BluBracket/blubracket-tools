# [BluBracket](https://blubracket.com/) CI/CD tools

## Setup

### Azure Pipelines
1. Put `ci-cd-scan.py` in the repository you would like to scan and add one step to your `azure-pipelines.yml`:
    ```
    - script: python build/ci-cd-scan.py 
      displayName: 'Scan for secrets'
      env:
        BLUBRACKET_CI_CD_TOKEN: $(BLUBRACKET_CI_CD_TOKEN)
    ```
2. In the Azure pipeline settings UI, set the two environment [variables](https://docs.microsoft.com/en-us/azure/devops/pipelines/process/variables) `BLUBRACKET_CI_CD_API` and `BLUBRACKET_CI_CD_TOKEN`:
    ```
    BLUBRACKET_CI_CD_API=https://<put your tenant name here>.blubracket.com/api/analyzer/commit/scan
    BLUBRACKET_CI_CD_TOKEN=<put your token here>
    ```
    It is recommended to set `BLUBRACKET_CI_CD_TOKEN` as a [secret variable](https://docs.microsoft.com/en-us/azure/devops/pipelines/process/variables#secret-variables) so that the token doesn't get exposed in the build logs.
