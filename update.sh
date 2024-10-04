#!/bin/bash

if [[ -n "$1" ]]; then
    if [[ -f "$1" ]]; then
        commit_description=" : $(cat $1)"
    else
        commit_description=" : $1"
    fi
fi

cat ../token.txt | xclip -selection clipboard

# Add all changes
git add .

# Commit with a message including the current date
git commit -m "Update $(date +%F)${commit_description}" 

# Push to the main branch
git push origin main
