import pandas as pd
from sentence_transformers import SentenceTransformer

def process_csv_and_save_embeddings(csv_filepath, output_filename):
    """
    Process a CSV file to add SBERT embeddings to each row and save as a .jsonl file.

    Parameters:
    - csv_filepath: Path to the CSV file to process.
    - output_filename: Name of the .jsonl file to save the output.
    """
    # Load CSV into DataFrame
    columns = ['topic', 'type', 'desc']
    df = pd.read_csv(csv_filepath, header=None, names=columns)

    # Initialize the SentenceTransformer model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Encode descriptions to get embeddings
    embeddings = model.encode(df['desc'].values)

    # Add embeddings to the DataFrame
    df['embeddings'] = list(embeddings)

    # Assign unique names based on index
    df['name'] = [f"op-ed_{i}" for i in range(len(df))]

    # Select relevant columns and export to .jsonl
    df[['name', 'desc', 'embeddings']].to_json(output_filename, orient='records', lines=True)
    print(f"Data saved to {output_filename}")

# Specify the path to your CSV file and the desired output .jsonl file name
csv_filepath = 'embed_ready_results.csv'
output_filename = 'results_with_embeddings.jsonl'

# Process the CSV file and save the embeddings
process_csv_and_save_embeddings(csv_filepath, output_filename)
