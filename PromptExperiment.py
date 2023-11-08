import itertools
import random


class PromptExperiment:
    """A class to perform Monte Carlo and factorial prompt experiments.

    Attributes:
        hyperparameters (dict): A dictionary with hyperparameter settings.
        N (int): The number of experiments to run.
        prompt_mode (str): The mode for running prompt experiments ('monte_carlo' or 'factorial').
        hyper_mode (str): The mode for running hyperparameter experiments ('monte_carlo' or 'factorial').
        prompts (list, optional): A list of prompts to use for a prompt-comparison experiment
        template_prompt (str, optional): A template prompt formatted like "It is {degrees} degrees outside" for a templated experiment
        prompt_parameters (dict, optional): A dictionary with parameter names as keys and lists of possible values as values for a templated experiment
        seed (int, default=416): A seed for the random number generator to ensure reproducibility.
    """

    def __init__(self, hyperparameters, N, prompt_mode='monte_carlo', hyper_mode='factorial', prompts=None,
                 template_prompt=None, prompt_parameters=None, seed=416):
        """Initializes the PromptExperiment with provided attributes."""

        if prompts is None:
            assert (template_prompt is not None and prompt_parameters is not None,
                    "If you are not entering a list of prompts you need to enter a template prompt and prompt parameters.")
            self.template_prompt = template_prompt
            self.prompt_parameters = prompt_parameters
        if prompts is not None:
            self.template_prompt = "{prompt}"
            self.prompt_parameters = {'prompt': prompts}

        self.hyperparameters = hyperparameters
        self.N = N
        self.prompt_mode = prompt_mode
        self.hyper_mode = hyper_mode
        self.seed = seed
        random.seed(self.seed)

    def generate_prompts(self):
        """Generates prompts based on the mode specified (monte_carlo or factorial).

        Returns:
            A list of prompt strings with the parameters filled in.
        """
        if self.prompt_mode == 'monte_carlo':
            return [self.template_prompt.format(**self.random_params(self.prompt_parameters)) for _ in range(self.N)]
        elif self.prompt_mode == 'factorial':
            return [self.template_prompt.format(**params) for params in self.factorial_params(self.prompt_parameters)]

    def generate_hyperparameters(self):
        """Generates hyperparameters based on the mode specified (monte_carlo or factorial).

        Returns:
            A list of hyperparameter dictionaries.
        """
        if self.hyper_mode == 'monte_carlo':
            return [self.random_params(self.hyperparameters) for _ in range(self.N)]
        elif self.hyper_mode == 'factorial':
            return self.factorial_params(self.hyperparameters)

    def run_experiments(self):
        """Runs the experiments based on the selected modes and collects responses.

        Returns:
            A list of tuples containing the prompt, parameters used, hyperparameters, and response.
        """
        results = []

        if self.prompt_mode == 'monte_carlo' and self.hyper_mode == 'monte_carlo':
            for _ in range(self.N):
                prompt_params = self.random_params(self.prompt_parameters)
                prompt = self.template_prompt.format(**prompt_params)
                hyperparams = self.random_params(self.hyperparameters)
                response = self.simulate_response(prompt, hyperparams)
                result = self.flatten_results(prompt, prompt_params, hyperparams, response)
                results.append(result)

        elif self.prompt_mode == 'factorial' and self.hyper_mode == 'monte_carlo':
            for prompt_params in self.factorial_params(self.prompt_parameters):
                prompt = self.template_prompt.format(**prompt_params)
                for _ in range(self.N):
                    hyperparams = self.random_params(self.hyperparameters)
                    response = self.simulate_response(prompt, hyperparams)
                    result = self.flatten_results(prompt, prompt_params, hyperparams, response)
                    results.append(result)

        elif self.prompt_mode == 'factorial' and self.hyper_mode == 'factorial':
            for prompt_params in self.factorial_params(self.prompt_parameters):
                prompt = self.template_prompt.format(**prompt_params)
                for hyperparams in self.factorial_params(self.hyperparameters):
                    response = self.simulate_response(prompt, hyperparams)
                    result = self.flatten_results(prompt, prompt_params, hyperparams, response)
                    results.append(result)

        elif self.prompt_mode == 'monte_carlo' and self.hyper_mode == 'factorial':
            for hyperparams in self.factorial_params(self.hyperparameters):
                for _ in range(self.N):
                    prompt_params = self.random_params(self.prompt_parameters)
                    prompt = self.template_prompt.format(**prompt_params)
                    response = self.simulate_response(prompt, hyperparams)
                    result = self.flatten_results(prompt, prompt_params, hyperparams, response)
                    results.append(result)

        return results

    def random_params(self, parameter_space):
        """Generates a random set of parameters from the given parameter space.

        Args:
            parameter_space (dict): A dictionary with parameter names as keys and lists of possible values as values.

        Returns:
            A dictionary mapping parameter names to random values from the parameter space.
        """
        return {param: random.choice(values) for param, values in parameter_space.items()}

    def factorial_params(self, parameter_space):
        """Generates a list of all possible parameter combinations using a factorial approach.

        Args:
            parameter_space (dict): A dictionary with parameter names as keys and lists of possible values as values.

        Returns:
            A list of dictionaries, each representing a unique combination of parameters.
        """
        return [dict(zip(parameter_space, values)) for values in itertools.product(*parameter_space.values())]

    def simulate_response(self, prompt, hyperparams):
        """Simulates a response from ChatGPT for demonstration purposes."""
        # Placeholder for actual API response
        return "Simulated response."

    def flatten_results(self, prompt, prompt_params, hyperparams, response):
        """Flattens the experiment result data into a single dictionary."""
        result = {'prompt': prompt, 'output': response}
        result.update({f'param_{k}': v for k, v in prompt_params.items()})
        result.update({f'hyper_{k}': v for k, v in hyperparams.items()})
        return result
