#!/bin/sh

function clean_up() {
    result=$?
    [ ! -z "$REPO_PATH" ] && rm -f $REPO_PATH/ci-cd-scan.py
    exit $result
}

trap clean_up EXIT

python --version

# Mount repo directory if not using 'SYSTEM_PULLREQUEST_PULLREQUESTNUMBER'
# example: docker run -v /git/linux:/linux -e REPO_PATH="/linux ..." 
if [ ! -z "$REPO_PATH" ] && [ -d "$REPO_PATH" ]; then
    echo "REPO_PATH: $REPO_PATH"
    cp -f ci-cd-scan.py $REPO_PATH
    cd $REPO_PATH
fi

echo "Starting CI-CD scan container"
python ci-cd-scan.py
