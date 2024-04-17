"""
This script generates responses for a set of tasks using the LiteLLM API and saves the responses to a CSV file.
To run the file, add a .env into the same folder that contains api keys.  .
"""
import pandas as pd
from litellm import LiteLLM, completion
import os
from dotenv import load_dotenv
import logging
from tqdm import tqdm


logging.basicConfig(filename=f"{os.path.splitext(os.path.basename(__file__))[0]}.log", level=logging.INFO, format='%(asctime)s: %(message)s', filemode='w', datefmt='%Y-%m-%d %H:%M:%S')

def initialize_lite_llm():
    """
    Initialize the LiteLLM with the API key from the .env file.
    """
    # Load environment variables from .env file
    load_dotenv()

    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
    os.environ["MISTRAL_API_KEY"] = os.getenv("MISTRAL_API_KEY")

    return LiteLLM()


def generate_responses(lite_llm, tasks, models, num_completions=3):
    """
    Generate responses for each task and model.
    """
    total_tasks = len(tasks) * len(models) * num_completions
    counter = 0
    new_data = []
    for task in tqdm(tasks, desc='tasks'):
        for model in models:
            for _ in range(num_completions):
                messages = [{"content": task["prompt"], "role": "user"}]
                response = completion(
                    model=model,
                    messages=messages,
                )
                response_text = response['choices'][0]['message']['content']
                new_data.append({
                    "model": model,
                    "category": task["category"],
                    "output": response_text,
                    "dataset_id": f"{model}_{task['category']}_{_}"
                })
                if counter % 10 == 0:
                    logging.info(f'Completed {counter} of {total_tasks} tasks')
                    print(response_text)
                counter += 1
    return new_data


def main():
    """
    Main function to run the entire process.
    """

    lite_llm = initialize_lite_llm()

    # Define your tasks, models, and number of completions here
    tasks = [
        {
            "category": "startup",
            "prompt": """INSTRUCTIONS
You are an expert startup founder. Return a one-line startup idea that would top Product Hunt.

CONSTRAINTS:
- Return an idea that could appear in Product Hunt
- Return a startup idea and nothing else

RETURN:
- Return a json file of an startup idea and nothing else like {"idea": idea}

"""
        },

        {
            "category": "oped",
            "prompt": """
INSTRUCTIONS:
You are an expert op-ed writer.  Return a headline for an op-ed that could appear in the New York Times.

CONSTRAINTS:
- Return a headline that could appear in the New York Times
- Return an op-ed headline and nothing else

RETURN:
- Return a json file of an op-ed headline and nothing else like {"headline": headline}
            """
        },

        {
            "category": "podcast",
            "prompt": """
INSTRUCTIONS:
Act like an expert podcaster. Come up with a podcast description that would be featured in Google podcasts.

CONSTRAINTS:
- Don't follow a specific structure
- Return a description and nothing else

RETURN:
- A json file of a podcast description and nothing else like {"description": "description"}
        """
        }
    ]

    models = ["gpt-3.5-turbo", "gpt-4-0613", "claude-2"]
    num_completions = 100
    new_data = generate_responses(lite_llm, tasks, models, num_completions)
    df = pd.DataFrame(new_data)
    df.to_json('responses.jsonl', lines=True, orient='records')


if __name__ == "__main__":
    main()
