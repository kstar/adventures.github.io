#!/bin/bash
perl -i -pe 's,\(\s*dso([^)]*)\s*\)((?:(?!\(dso).)+)\(\s*dso\s*\),my $temp = $1; my $tmp2 = $2; $temp =~ s/simbad:(.+)$/simbad="\1"/; $tmp2 =~ s/\\-/-/; "<x-dso" . $temp . ">" . $tmp2 . "</x-dso>",ge' $@
