#!/bin/bash
#

if [[ $(basename $(pwd)) != "docs" ]]; then
    >&2 echo "Please execute in the docs/ folder"
    exit 1;
fi;

if [ -z $1 ]; then
    >&2 echo "Usage: $0 <new version number>"
    exit 1;
fi;

ver=$1

echo "Updating to version ${ver}"

ls *.htm* _layouts/*.htm* _includes/*.htm* | ../scripts/parallel_perl.sh 's:css\?version=\d+:css?version='${ver}':'
