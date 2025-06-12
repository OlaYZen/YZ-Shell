#!/bin/bash

echo "This will permanently delete YZ-Shell cache, configuration, and remove its entry from hyprland.conf."
read -p "Are you sure you want to continue? [y/N] " confirm

if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted."
    exit 1
fi

rm -rf ~/.cache/yz-shell
rm -rf ~/.config/YZ-Shell

conf_file=~/.config/hypr/hyprland.conf
tmp_file=$(mktemp)

awk '
BEGIN { found_comment=0 }
{
    if ($0 ~ /# YZ-Shell/) {
        found_comment=1
        next
    }
    if (found_comment && $0 ~ /source[[:space:]]*=[[:space:]]*~\/\.config\/YZ-Shell\/config\/hypr\/yz-shell\.conf/) {
        found_comment=0
        next
    }
    print
}' "$conf_file" > "$tmp_file" && mv "$tmp_file" "$conf_file"

echo "YZ-Shell data and config removed successfully."
