#!/bin/bash
perl -CSAD -i -pe 's,\(\s*dso([^)]*)\s*\\?\)((?:(?!\(dso).)+)\\?\(\s*dso\s*\),my $temp = $1; my $tmp2 = $2; $temp =~ s/simbad: *["\x{FF02}\x{201C}\x{201D}\x{201E}]?((?:.(?! omit| noindex))+)(?:["\x{FF02}\x{201C}\x{201D}\x{201E}]|\b)/my $temp3 = $1; $temp3 =~ s:\\([+-\.]):\1:g; "simbad=\"" . $temp3 . "\""/uge; $temp =~ s:\\$::; $tmp2 =~ s/\\([+-])/\1/g; " <x-dso" . $temp . ">" . $tmp2 . "</x-dso> ",ge' $@
perl -i -pe 's:<x-dso([^>]*)>\*\*(.+)\*\*</x-dso>:<b><x-dso\1>\2</x-dso></b>:g' $@

