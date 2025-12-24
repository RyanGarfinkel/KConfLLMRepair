from src.llm.prompt import get_prompt
from google.genai import types
from google import genai
import time
import json
import re

max_retries = 2
default_delay = 30

client = genai.Client()

model = 'gemini-2.5-flash'

config = types.GenerateContentConfig(
    max_output_tokens=16384,
)

def extract_retry_delay(error_message):
    match = re.search(r'retry in (\d+\.?\d*)s', error_message)
    
    if match:
        return float(match.group(1)) + 1
    
    return default_delay

def get_suggestions(delta):

    tries = 0
    while True:

        if tries >= max_retries:
            print('Max retries reached. Aborting LLM request.')
            return {}
        
        tries += 1
        
        print('Prompting LLM for repair suggestions...')

        prompt = get_prompt(delta)

        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )

            print('LLM repair suggestions received. Parsing response...')
            text = response.text.strip()

            if text.startswith('```json'):
                text = text[7:]
            
            if text.endswith('```'):
                text = text[:-3].strip()

            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)
            else:
                print('No JSON object found in LLM response.')
                return {}
            
            suggestions = json.loads(text)

            print('LLM response parsed successfully.')

            return suggestions
        except Exception as e:

            if '429 RESOURCE_EXHAUSTED' in str(e):
                delay = extract_retry_delay(str(e))
                if delay is None:
                    delay = default_delay

                print(f'Rate limit encountered. Retrying in {delay} seconds...')
                time.sleep(delay)
            else:
                print('Error during LLM request or parsing:', e)
                return {}
