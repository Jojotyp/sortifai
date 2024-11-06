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

model_content = "You are an image sorting assistant. You look at the given image and classify it into one of the given categories."
prompt = "... The category that fits the best will be your choice."

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "assistant", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What’s in this image?"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                    },
                },
            ],
        }
    ],
    max_tokens=300,
)

print(response.choices[0].message.content)
