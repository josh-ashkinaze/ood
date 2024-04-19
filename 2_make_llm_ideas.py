"""
This script generates responses for a set of tasks using the LiteLLM API and saves the responses. 
To run the file, add a `.env` with API keys in the same folder that contains this script.
"""
import pandas as pd
import litellm
from litellm import completion
import os
from dotenv import load_dotenv
import logging
from tqdm import tqdm
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type
from litellm.exceptions import RateLimitError


logging.basicConfig(filename=f"{os.path.splitext(os.path.basename(__file__))[0]}.log", level=logging.INFO, format='%(asctime)s: %(message)s', filemode='w', datefmt='%Y-%m-%d %H:%M:%S')

def initialize_lite_llm():
    """
    Initialize the LiteLLM with the API key from the .env file.
    """
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
    os.environ["MISTRAL_API_KEY"] = os.getenv("MISTRAL_API_KEY")

@retry(retry=retry_if_exception_type(RateLimitError), wait=wait_fixed(60), stop=stop_after_attempt(10))
def safe_completion(task, model):
    """
    Safely complete the task using the specified model, handling rate limits.
    """
    messages = [{"content": task["prompt"], "role": "user"}]
    try:
        response = completion(
            model=model,
            messages=messages,
        )
        response_text = response['choices'][0]['message']['content']
        return response_text
    except Exception as e:
        logging.info(f"Error during completion: {str(e)}")
        raise

def generate_responses(tasks, models, num_completions=3):
    """
    Generate responses for each task and model.
    """
    total_tasks = len(tasks) * len(models) * num_completions
    counter = 0
    new_data = []
    for task in tqdm(tasks, desc='Tasks'):
        for model in models:
            for _ in range(num_completions):
                try:
                    response_text = safe_completion(task, model)
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
                except Exception as e:
                    logging.info(f"Failed to process task: {task['category']} with model: {model}. Error: {str(e)}")
    return new_data



def main():
    """
    Main function to run the entire process.
    """

    initialize_lite_llm()

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
- Return a json file of a podcast description and nothing else like {"description": "description"}
        """
        }
    ]

    litellm.set_verbose = False
    models = ["gpt-3.5-turbo", "gpt-4-0613", "claude-2"]
    num_completions = 100
    logging.info('Starting generation of responses')
    logging.info("Params" + str(tasks) + str(models) + str(num_completions))
    new_data = generate_responses(tasks, models, num_completions)
    df = pd.DataFrame(new_data)
    df.to_json('ai_ideas.jsonl', lines=True, orient='records')


if __name__ == "__main__":
    main()
