import pandas as pd
from litellm import LiteLLM, completion
import os
from dotenv import load_dotenv
import random

def initialize_lite_llm():
    """
    Initialize the LiteLLM with the API key from the .env file.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in the .env file.")
    
    os.environ["OPENAI_API_KEY"] = api_key
    return LiteLLM()

def load_word_counts(file_name):
    """
    Load word counts from a given CSV file and return as a list.
    """
    df = pd.read_csv(file_name)
    return df['wc'].tolist()

def generate_responses(lite_llm, tasks, models, num_completions=3):
    """
    Generate responses for each task and model. Adjust to use random word count from task's distribution.
    """
    new_data = []
    for task in tasks:
        word_counts = task["word_count"]
        for model in models:
            for _ in range(num_completions):
                random_wc = random.choice(word_counts) if word_counts else None
                messages = [{"content": task["prompt"], "role": "system"}]
                response = completion(
                    model=model,
                    messages=messages,
                    max_tokens=600 # Adjust as needed
                )
                response_text = response['choices'][0]['message']['content']
                if random_wc:
                    words = response_text.split()[:random_wc]
                    response_text = " ".join(words)
                new_data.append({"model": model, "category": task["category"], "output": response_text})
    return new_data

def save_responses(new_data, csv_path='system_results.csv'): # Change csv path here
    """
    Save new unique responses to the CSV file, ensuring no duplicates.
    """
    try:
        existing_df = pd.read_csv(csv_path)
    except FileNotFoundError:
        existing_df = pd.DataFrame(columns=['model', 'category', 'output'])
    
    new_df = pd.DataFrame(new_data)
    updated_df = pd.concat([existing_df, new_df]).drop_duplicates(['model', 'category', 'output'])
    updated_df.to_csv(csv_path, index=False)
    updated_df.to_csv(csv_path, index=False)

    print(f"CSV file has been updated with {len(new_df)} new unique model responses.")

def main():
    lite_llm = initialize_lite_llm()

    # Load word counts for each domain
    fiction_wc = load_word_counts("oped_word_counts.csv")
    startups_wc = load_word_counts("startups_word_counts.csv")

    # Define your tasks, models, and number of completions here
    tasks = [
        {
            "category": "startup idea",
            "prompt": "INSTRUCTIONS: Give me a startup idea that would appear on Product Hunt. CONTEXT: blah. CONSTRAINTS: Make sure the response is N words. Vary the structure of the idea. Don't follow a specific structure like introducing the name first.",
            "word_count": startups_wc
        },
        {
            "category": "NYT Headlines",  
            "prompt": "INSTRUCTIONS: You are the chief editor of New York Times. Write a one-sentence op-ed. CONTEXT: Challenge and engage audiences. CONSTRAINTS: Make sure your response is 10-15 words. Vary the structure.",
            "word_count": fiction_wc  # Using the correct variable name now
        }
    ]
    models = ["gpt-4"]
    num_completions = 100  # Adjusted for your requirement of 200 generations per domain
    new_data = generate_responses(lite_llm, tasks, models, num_completions)
    save_responses(new_data)

if __name__ == "__main__":
    main()
