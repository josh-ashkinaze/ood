import json
import pickle
import os
import glob
import logging
from sentence_transformers import SentenceTransformer

# Setup logging
LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
logging.basicConfig(filename='embedding_generation.log', level=logging.INFO, format=LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S', filemode='w')

def find_latest_files(prefixes, directory='.'):
    """
    Find the latest file for each given prefix in the specified directory.
    """
    latest_files = {}
    for prefix in prefixes:
        search_pattern = os.path.join(directory, f'{prefix}_*.jsonl')
        files = glob.glob(search_pattern)
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        if files:
            latest_files[prefix] = files[0]
            logging.info(f'Latest file for prefix "{prefix}": {files[0]}')
        else:
            logging.warning(f'No files found for prefix "{prefix}"')
    return latest_files

def load_jsonl(file_path):
    """
    Load data from a JSONL file.
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            entry = json.loads(line)
            data.append((entry['dataset_id'], entry['description']))
    return data

def generate_embeddings(data, model):
    """
    Generate SBERT embeddings for the given data.
    """
    sentences = [entry[1] for entry in data]
    return model.encode(sentences)

def process_file(file_path, model):
    """
    Process a given file to generate and store embeddings.
    """
    logging.info(f'Start processing file: {file_path}')
    data = load_jsonl(file_path)
    embeddings = generate_embeddings(data, model)
    output_file = f'{file_path}_embeddings.pkl'
    with open(output_file, "wb") as fOut:
        pickle.dump({'data': data, 'embeddings': embeddings}, fOut, protocol=pickle.HIGHEST_PROTOCOL)
    logging.info(f'Completed processing file: {file_path}. Output stored in {output_file}')

def main():
    """
    Main function to process files and generate embeddings.
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')
    prefixes = ['fiction', 'startups', 'preprints']
    latest_files = find_latest_files(prefixes)
    for file_path in latest_files.values():
        process_file(file_path, model)

if __name__ == "__main__":
    main()
