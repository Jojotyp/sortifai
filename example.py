import os
from dotenv import load_dotenv
import openai

# Load the .env file
load_dotenv()

# Get the OpenAI API key from the environment variables
api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client with the API key
openai.api_key = api_key

# Test request to verify if the key is loaded successfully
client = openai.OpenAI()

completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Write a haiku about recursion in programming."
        }
    ],
    max_tokens=400,
)

print(completion.choices[0].message)