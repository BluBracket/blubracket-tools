#!/bin/sh

python --version

# Mount repo directory if not using 'SYSTEM_PULLREQUEST_PULLREQUESTNUMBER'
# example: docker run -v /git/linux:/linux -e REPO_PATH="/linux ..." 
if [ ! -z "$REPO_PATH" ] && [ -d "$REPO_PATH" ]; then
    echo "found REPO_PATH $REPO_PATH"
    cp ci-cd-scan.py $REPO_PATH
    cd $REPO_PATH
fi

echo "Starting CI-CD scan container"
python ci-cd-scan.py

# clean up
[ ! -z "$REPO_PATH" ] && rm $REPO_PATH/ci-cd-scan.py
