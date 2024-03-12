"""
Author: Yan Liu
Date: 2024-03-12

Description: Data checker

"""

import json
import pandas as pd
import numpy as np

import json
import pandas as pd
import numpy as np

# Load your JSON Lines data
def load_jsonl(filepath):
    data = []
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            data.append(json.loads(line))
    return data


# Convert loaded data to DataFrame
def json_to_dataframe(json_data):
    df = pd.DataFrame(json_data)
    return df


# Define the problematic description identification function
def is_problematic(description,title, percentile_threshold):

    # 1. no description in that json
    if not description or description == "":
        return True
    if description == title:
        return True
    
    if isinstance(description, str):
        words = description.split()
        
        # 2. just a link
        # 3. a single line

        if description.startswith('http://') :
            return True
        
        # 4. the same name as the title
        # More checking needed here to determine it's problematic


        # Check if the word count is above the overall 10th percentile threshold
        if len(words) > percentile_threshold:
            return False  
    return False
  

# Calculate the 10th percentile for word count in all descriptions
def calculate_percentile_threshold(df):
    percentile_threshold = np.percentile(df['description'].str.split().apply(len), 10)
    return percentile_threshold

# Main function
def main(filepath):
    data = load_jsonl(filepath)
    df = json_to_dataframe(data)

    sampled_df = df.sample(n=30, random_state=None)
    
    # Calculate the overall 10th percentile threshold for all descriptions
    percentile_threshold = calculate_percentile_threshold(df)

    # Apply the problematic description identification function on the sampled data
    sampled_df['is_problematic'] = sampled_df.apply(lambda row: is_problematic(row['description'], row['title'], percentile_threshold), axis=1)
    
    # Print the samples along with whether they are problematic or not
    print(sampled_df[['description', 'title', 'is_problematic']])

if __name__ == "__main__":
    filepath = 'pilot__2023-01-01_to_2023-03-01_podcasts.jsonl'
    main(filepath)
