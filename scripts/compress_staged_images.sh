git diff --name-only --cached | grep 'docs/assets' | xargs stat -c '%s %n' | grep -E '^[0-9]{6}' | cut -d' ' -f2 | parallel --bar 'cp {} {}.bak && mogrify -resize 800x600\> -quality 87 {}'
