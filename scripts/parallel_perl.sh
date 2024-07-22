#!/bin/bash
# Runs the supplied (argument) PCRE in-place on the list of files supplied on stdin
parallel 'perl -i -pe '"'${1}'"' {}'
