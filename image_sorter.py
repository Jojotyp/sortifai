"""
Sort images 
"""

import os
import json
import shutil
import base64
from dotenv import load_dotenv
import openai
# from PIL import Image

# Define paths
source_folder = "/home/fabi/Documents/Fabi/Pictures/phone/Screenshots_test"  # Path to the folder containing images to be categorized
output_folder = "/home/fabi/Documents/Fabi/Pictures/phone/output"
failed_folder = os.path.join(output_folder, "failed")


# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

# Load categories from JSON file
with open("categories.json", "r") as f:
    categories = json.load(f)


# Step 1: Create output folders for each category
os.makedirs(output_folder, exist_ok=True)
print('created output folder at: ' + output_folder)

for category in categories:
    os.makedirs(os.path.join(output_folder, category["folder_name"]), exist_ok=True)
    print(f'created folder "{category["folder_name"]}" at: ' + output_folder + '/' + category["folder_name"])

os.makedirs(failed_folder, exist_ok=True)
print('created failed classification folder at: ' + failed_folder)


# Step 2: Prepare categories context for the model
categories_context = "\n".join([
    f"Category: {cat['category']}, Description: {cat['description']}"
    for cat in categories
])

print(f'\n\ncategories_context:\n{categories_context}')


# TODO: The classification is not working because the response message does not consist of the exact category names.
# To fix this we need to maybe get a strict response: https://platform.openai.com/docs/guides/structured-outputs

# Step 3: Loop over images in the source folder
print('\n\nLooping over images...')
for image_name in os.listdir(source_folder):
    image_path = os.path.join(source_folder, image_name)
    
    # Skip non-image files
    if not os.path.isfile(image_path) or not image_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        print(f'Skipped file: {image_name}')
        continue

    # Encode image in base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    # Step 4: Prepare prompt for the model
    prompt = f"Given the following categories:\n{categories_context}\n\nDetermine which category the following image belongs to:"
    
    # Send request to OpenAI API
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=100,
    )

    # Extract the model's response
    category_name = response.choices[0].message.content.strip()
    print(f'Classified {image_name} as: {category_name}')

    # Step 5: Check if the response is a valid category
    valid_category = next((cat for cat in categories if cat["category"] == category_name), None)
    print(f'is valid category? {valid_category}\n-----')
    
    if valid_category:
        # Step 5.a: Copy image to the appropriate folder
        target_folder = os.path.join(output_folder, valid_category["folder_name"])
        shutil.copy(image_path, target_folder)
    else:
        # Step 5.b: Copy image to the "failed" folder
        shutil.copy(image_path, failed_folder)

print("Image classification completed.")
