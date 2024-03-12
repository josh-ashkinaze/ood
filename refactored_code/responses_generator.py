# responses_generator.py
'''
This script generates responses for a set of tasks using the LiteLLM API and saves the responses to a CSV file.
To run the file, add a .env into the same folder that contains the variable OPENAI_API_KEY = 'your api key', 
then run the python file to create and add to a csv file called responses.csv
(this already exists in the main folder and contains around 200 results)
To change the prompts, go to the tasks dictionary.
'''
import pandas as pd
from litellm import LiteLLM, completion
import os
from dotenv import load_dotenv


def initialize_lite_llm():
    """
    Initialize the LiteLLM with the API key from the .env file.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Retrieve the API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in the .env file.")
    
    os.environ["OPENAI_API_KEY"] = api_key
    return LiteLLM()


def generate_responses(lite_llm, tasks, models, num_completions=3):
    """
    Generate responses for each task and model.
    """
    
    new_data = []
    for task in tasks:
        for model in models:
            for _ in range(num_completions):
                messages = [{"content": task["prompt"], "role": "user"}]
                response = completion(
                    model=model,
                    messages=messages,
                    max_tokens=500
                )
                response_text = response['choices'][0]['message']['content']

                if task["word_count"]:
                    words = response_text.split()[:task["word_count"]]
                    response_text = " ".join(words)

                new_data.append({"model": model, "category": task["category"], "output": response_text})
    return new_data

def save_responses(new_data, csv_path='responses.csv'):
    """
    Save new unique responses to the CSV file, ensuring no duplicates.
    """
    try:
        existing_df = pd.read_csv(csv_path)
    except FileNotFoundError:
        existing_df = pd.DataFrame(columns=['model', 'category', 'output'])
    
    # Convert new_data to DataFrame and merge with existing
    new_df = pd.DataFrame(new_data)
    updated_df = pd.concat([existing_df, new_df]).drop_duplicates(['model', 'category', 'output'])
    updated_df.to_csv(csv_path, index=False)
    print(f"CSV file has been updated with {len(new_df)} new unique model responses.")

def main():
    """
    Main function to run the entire process.
    """
   
    lite_llm = initialize_lite_llm()

    # Define your tasks, models, and number of completions here
    tasks = [
        {
        "category": "startup idea",
        "prompt": "INSTRUCTIONS: Give me a startup idea that would appear on Product Hunt. CONTEXT: blah. CONSTRAINTS: Make sure the response is N words. Vary the structure of the idea. Don't follow a specific structure like introducing the name first.",
        "word_count": None  # Adjust based on the task
    },
    {
        "category": "op-ed",
        "prompt": "INSTRUCTIONS: You are the chief editor of New York Times. Write a one-sentence op-ed. CONTEXT: Challenge and engage audiences. CONSTRAINTS: Make sure your response is 10-15 words. Vary the structure.",
        "word_count": 15  # Example adjustment
    },
    {
        "category": "Fiction",
        "prompt": """
        INSTRUCTIONS: give me an introduction of a short fiction piece. 
        CONTEXT: - Give your story strong dramatic content Vary rhythm and structure in your prose Create believable, memorable characters Make the important story sections effective Deepen your plot with subplots Make every line of dialogue count Add what makes a good story (immersive setting) Create conflict and tension Craft beguiling beginnings Deliver knockout endings 
        CONSTRAINTS: - Make sure the response is 50 words - Vary the structure of the introduction - Don't follow a specific structure like introducing the name first.
        """,
        "word_count": 50
    },
    {
        "category": "Podcasts",
        "prompt": """
        INSTRUCTIONS: give me an intro to a podcast that would be featured in Google podcasts. 
        CONTEXT: -To give your podcast the best start in life, it needs to be different from the rest. And it needs to offer listeners something that other shows don’t. Having a unique premise will help you stand out in the sea of noise. Good podcasts are built around one idea or concept, and they stick to it. They don’t try to please everyone. - Whether your podcast’s aim is to educate, inform, or entertain, shows that typically give listeners value are the best ones. What do you want people to take away from your show? And what are they actually coming to you in search of? The better you can satisfy their needs, the more likely you are to win them over. 
        CONSTRAINTS: - Make sure the response is 50 words - Vary the structure of the introduction - Don't follow a specific structure like introducing the name first.
        """,
        "word_count": 50
    } 
    ]
    models = ["gpt-3.5-turbo", "gpt-4-0613"]
    num_completions = 3

    new_data = generate_responses(lite_llm, tasks, models, num_completions)
    save_responses(new_data)

if __name__ == "__main__":
    main()
