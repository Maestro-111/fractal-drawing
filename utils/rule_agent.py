import itertools
import json
import os
import sys
import threading
import time

import openai
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


class RuleAgent:

    """ """

    def __init__(self, logger):
        self.logger = logger
        openai.api_key = os.environ.get("OPENAI_API_KEY")

    def _save_to_json(self, data, file_path):
        """
        Save data to a JSON file.

        Args:
            data: Dictionary to save
            file_path: Path where to save the file
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved L-system to: {file_path}")

        except Exception as e:
            self.logger.error(f"Error saving JSON to {file_path}: {e}")

    def generate_prompt(
        self, base_template: dict, entity: str, variation_style="similar"
    ):
        """
        Generate a prompt for LLM to create L-system variations.

        Args:
            base_template: The original L-system template dict
            entity: e.g., "tree", "flower", "fern"
            variation_style: "similar", "creative", "extreme"
        """

        variation_instructions = {
            "similar": "Create a subtle variation that maintains the core structure but adds minor differences",
            "creative": "Create a more distinct variation with different branching patterns and parameters",
            "extreme": "Create a dramatically different variation with experimental rules and structures",
        }

        prompt = f"""You are an expert in L-systems (Lindenmayer systems) for procedural generation.
    Your task is to generate a new variation of a {entity} L-system.

    BASE TEMPLATE:
    {json.dumps(base_template, indent=2)}

    INSTRUCTIONS:
    {variation_instructions.get(variation_style, variation_instructions["similar"])}

    RULES FOR GENERATION:

    1. Rules must follow this structure:
       - "pattern": The symbol to match (e.g., "A", "F", "FT(x,y)")
       - "replacement": What to replace it with (use valid L-system commands)
       - "probability": Float between 0 and 1 (probabilities for same pattern should sum to ≤1)
       - "axiom": true if this rule applies to axiom symbols, false otherwise
       - "is_parametric": true if the rule uses parameters like x, y

    2. Valid L-system commands:
       - Drawing Symbols and their color:
            FT(x,y) or just FT: 'rgb(92, 51, 23)', where x is segment length and y is segment width
            F(x,y) or just F: 'rgb(50, 50, 50)', where x is segment length and y is segment width
            A(x,y): 'rgb(100, 100, 100)', where x is segment length and y is segment width
            B(x,y): 'rgb(150, 150, 150)', where x is segment length and y is segment width
            X(x,y): 'rgb(80, 80, 80)', where x is segment length and y is segment width
            Y(x,y): 'rgb(180, 180, 180)', where x is segment length and y is segment width
       - +(x): Turn left by angle by x
       - -(x): Turn right by angle by x
       - [: Push state (save position/angle)
       - ]: Pop state (restore position/angle)

    3. Parameters in rules can use:
       - Basic math: x*1.2, x+5, x/2
       - random.triangular(min, max, mode)
       - random.gauss(mean, stddev)
       - random.uniform(min, max)

    4. Adjust params reasonably according to the requested entity:
       - length: 5-50 (affects size)
       - width: 0.5-5 (affects thickness)
       - angle: 10-45 (affects branching angle)
       - iterations: keep iterations the same as it is in the original entity

    OUTPUT FORMAT:
    Return ONLY a valid JSON object with the exact same structure as the base template. Include:
    - base_axiom
    - rules (array of rule objects)
    - params (with length, width, angle, iterations)
    - supports_color (boolean)

    Do not include any explanation or markdown formatting - only the raw JSON object."""

        return prompt

    #
    # def generate_random_object_with_openai(self, prompt:str, save_path:str):
    #
    #     """
    #     """
    #
    #     try:
    #
    #         response = openai.chat.completions.create(
    #             model="gpt-4",
    #             messages=[{"role": "user", "content": prompt}],
    #             temperature=0.8,
    #         )
    #
    #         content = response.choices[0].message.content.strip()
    #
    #         extracted_data = json.loads(content)
    #
    #         self.logger.info(f"Generated variation successfully")
    #         self.logger.info(f"Generated Random Object: {extracted_data}")
    #
    #         self._save_to_json(extracted_data, save_path)
    #
    #         return extracted_data
    #
    #
    #     except json.JSONDecodeError as e:
    #
    #         self.logger.error(f"JSON parsing error: {e}")
    #         self.logger.error(f"Response was: {content}")
    #
    #         return {}
    #
    #     except Exception as e:
    #         self.logger.error(f"Error generating with LLM: {e}")
    #
    #         return {}

    def _spinner(self, message, stop_event):
        """Display a spinner while waiting."""
        spinner = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
        while not stop_event.is_set():
            sys.stdout.write(f"\r{message} {next(spinner)}")
            sys.stdout.flush()
            time.sleep(0.1)

    def generate_random_object_with_openai(self, prompt: str, save_path: str):
        """
        Generate L-system with visual feedback during API call.
        """
        try:
            # Start spinner in separate thread
            stop_spinner = threading.Event()
            spinner_thread = threading.Thread(
                target=self._spinner,
                args=("Generating L-system variation", stop_spinner),
            )
            spinner_thread.start()

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
            )

            # Stop spinner
            stop_spinner.set()
            spinner_thread.join()
            print("\r" + " " * 50 + "\r", end="")  # Clear spinner line

            content = response.choices[0].message.content.strip()
            self.logger.info(content)

            extracted_data = json.loads(content)
            self.logger.info("Generated variation successfully")
            self.logger.info(f"Generated Random Object: {extracted_data}")

            self._save_to_json(extracted_data, save_path)
            return extracted_data

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {e}")
            self.logger.error(f"Response was: {content}")
            return {}

        except Exception as e:
            self.logger.error(f"Error generating with LLM: {e}")
            return {}
