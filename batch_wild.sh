#!/bin/bash

# Specify the path to the CSV file
csv_file_path="dataset/wild/data.csv"

# Check if the file exists
if [[ ! -f "$csv_file_path" ]]; then
    echo "The specified CSV file does not exist."
    exit 1
fi

# Read the CSV file line by line
while IFS=, read -r address platform
do
    # Run the Python command with the extracted address and platform, and log the output
    python3 main.py -a "$address" -bp "$platform" -d "result/wild_1018" -v > "experiment_logset/wild_1018/${address}.log" 2>&1 &
done < "$csv_file_path"

# Wait for all background processes to finish
wait
