#!/bin/bash

# Specify the path to the CSV file
csv_file_path="dataset/wild/dataset.csv"

# Check if the file exists
if [[ ! -f "$csv_file_path" ]]; then
    echo "The specified CSV file does not exist."
    exit 1
fi

# Counter for tracking number of active processes
active_processes=0
max_concurrent_processes=16

# Read the CSV file line by line
while IFS=, read -r name address platform
do
    # Run the Python command with the extracted address and platform, and log the output
    python3 main.py -a "$address" -bp "$platform" -d "result/wild_1205" -n "$name" -v > "experiment_logset/wild_1205/${address}.log" 2>&1 &
    let active_processes+=1

    # Check if the maximum number of concurrent processes is reached
    if [[ $active_processes -ge $max_concurrent_processes ]]; then
        # Wait for any process to finish
        wait -n
        let active_processes-=1
    fi
done < "$csv_file_path"

# Wait for any remaining background processes to finish
wait
