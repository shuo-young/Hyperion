#!/bin/bash

# Specify the path to the CSV file
csv_file_path="dataset/ground_truth/dataset.csv"

# Check if the file exists
if [[ ! -f "$csv_file_path" ]]; then
    echo "The specified CSV file does not exist."
    exit 1
fi

# Counter for tracking number of processed files
counter=0
batch_size=16

# Read the CSV file line by line
while IFS=, read -r name address platform
do
    # Run the Python command with the extracted address and platform, and log the output
    python3 main.py -a "$address" -bp "$platform" -d "result/ground_truth" -n "$name" -v > "experiment_logset/ground_truth/${address}.log" 2>&1 &
    let counter+=1

    # Check if the batch size is reached
    if [[ $counter -eq $batch_size ]]; then
        # Wait for all background processes in this batch to finish
        wait
        # Reset counter
        counter=0
    fi
done < "$csv_file_path"

# Wait for any remaining background processes to finish
wait