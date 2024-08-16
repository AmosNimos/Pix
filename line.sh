#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 filename start_line end_line"
    exit 1
fi

# Assign arguments to variables
filename="$1"
start_line="$2"
end_line="$3"

# Use sed to print the specified range of lines
sed -n "${start_line},${end_line}p" "$filename"
