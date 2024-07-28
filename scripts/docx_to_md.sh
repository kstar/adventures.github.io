#!/bin/bash

[ -z "$1" ] && { >&2 echo "Usage: $0 <docx_file>"; exit 1; }

# TODO: Make this run on Windows too if needed
DOCS_DIR=$(dirname $0)"/../docs"
ASSETS_DIR=${DOCS_DIR}/assets
TARGET_MD=${DOCS_DIR}/$(echo $1 | sed 's:\.[^\.]*$::').md

if [ -f "${TARGET_MD}" ]; then
    >&2 echo "Target markdown file ${TARGET_MD} already exists. Will not overwrite.";
    exit 0;
fi

[ -d "./media/" ] && { >&2 echo "Warning: folder named \`media\` already exists; Quitting." ; exit 1; }

TEMP_MD="temp.md"

[ -f ${TEMP_MD} ] && { >&2 echo "Error: Will not overwrite ${TEMP_MD}. Quitting."; exit 1; }

set -x
pandoc -f docx -t gfm --extract-media="." -o ${TEMP_MD} "$1"

find media/ -type f | parallel 'TARGET_FN=$(shasum {} | cut -d'"'"' '"'"' -f1)"{= s:^.*(\.[^\.]*)$:\1: =}"; echo "Renaming embedded image {} to ${TARGET_FN}"; perl -i -pe '"'"'s:src="\./{}":src="assets/'"'"'${TARGET_FN}'"'"'":g'"'"' '${TEMP_MD}' && mv {} media/${TARGET_FN}'

echo "Guessing title and author and generating Jekyll front-matter"

echo -e "---\nlayout: default" > front_matter.tmp
echo -e "title:\nauthor:\n" | paste - <(grep -m 2 . ${TEMP_MD}) | tr '\t' ' ' >> front_matter.tmp
echo -e "---\n" >> front_matter.tmp
# FIXME: Remove the extracted lines that were used to make the front-matter so they don't repeat
cat front_matter.tmp ${TEMP_MD} > ${TEMP_MD}.tmp && mv ${TEMP_MD}.tmp ${TEMP_MD}
rm -f front_matter.tmp

echo "Moving markdown file to ${TARGET_MD} and media files to ${ASSETS_DIR}";
mv ${TEMP_MD} "${TARGET_MD}"
find media/ -type f | parallel 'mv {} '"${ASSETS_DIR}"'/'
rmdir media

set +x
