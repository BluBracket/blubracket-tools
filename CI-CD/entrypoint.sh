#!/bin/sh

count=0

function message() {
    echo "please pass '-e $1=[value_goes_here]' within the docker command"
    count=$((count+1))
}

[ -z "$BLUBRACKET_CI_CD_API" ] && message BLUBRACKET_CI_CD_API
[ -z "$BLUBRACKET_CI_CD_TOKEN" ] && message BLUBRACKET_CI_CD_TOKEN
[ -z "$BUILD_REPOSITORY_URI" ] && message BUILD_REPOSITORY_URI

if [ "$count" > "0" ]; then
    echo "Container failed to start, missing '$count' variable(s), please review documentation"
    #exit 1
fi

python --version

echo "Starting container"

exec "python ci-cd-scan.py"
