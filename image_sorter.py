"""
Sort images of a given source_folder into a given output_folder by categories defined in a categories.json file.
"""

import base64
import json
import os
import pprint
import shutil
from enum import Enum

import openai
from dotenv import load_dotenv
from pydantic import BaseModel
from python_utils.time_operations import timestamp


# TODO: possibly build an own assistant
# (https://platform.openai.com/assistants)
# (https://platform.openai.com/docs/assistants/overview)
# to reduce query length by giving the context of the categories to the assistant before querying.


# Define paths
source_folder = "/home/fabi/Pictures/phone/Screenshots"  # Path to the folder containing images to be categorized
output_folder = "/home/fabi/Pictures/phone/Screenshots_sorted" # target folder
failed_folder = os.path.join(output_folder, "failed")


# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

# Load categories from JSON file
with open("categories.json", "r") as f:
    categories = json.load(f)

for cat in categories:
    print(cat['category'])

# Create a dictionary of category names to use in the Enum
categories_dict = {item['category']: item['category'] for item in categories}

# Dynamically create the Enum class
# essentially this is (category names are the values of "category" keys in category objects of categories.json):
# class Category(str, Enum):
#     first_category = "first_category"
#     second_category = "second_category"
#     ...
#     nth_category = "nth_category"
CategoryEnum = Enum('Category', categories_dict)
print(f'CategoryEnum:\n{CategoryEnum}\n\n')


class CategoryDecisionReasoning(BaseModel):
    """
    This is the response_format to ensure a structured output of the model.
    https://platform.openai.com/docs/guides/structured-outputs

    It basically prevents the model from rambling without giving a clear answer.
    """
    category: CategoryEnum
    reasoning: str
    # TODO?: certainty between 0-1?


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


# Step 3: collect already into output dir sorted images to exclude those from classification
sorted_images = set()

# Traverse all category folders to collect sorted images
for category in categories:
    category_folder = os.path.join(output_folder, category["folder_name"])
    if os.path.exists(category_folder):
        sorted_images.update(os.listdir(category_folder))

# Also include images in the "failed" folder
if os.path.exists(failed_folder):
    sorted_images.update(os.listdir(failed_folder))

print(f'Found {len(sorted_images)} already sorted images to exclude from classification (duplicate classification).')


# Step 4: Loop over images in the source folder
output_json: list[dict] = []
images_dir = os.listdir(source_folder)

print('\n\nLooping over images...')
for i, image_name in enumerate(images_dir):
    print(f'Processing image nr. {i + 1}/{len(images_dir)}: {image_name}')

    # Skip images that have already been sorted
    if image_name in sorted_images:
        print(f'Skipped already sorted image: {image_name}')
        continue

    image_path = os.path.join(source_folder, image_name)

    # Skip non-image files
    if not os.path.isfile(image_path) or not image_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        print(f'Skipped non-image file: {image_name}')
        continue


    # Encode image in base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    # Step 5: Prepare prompt for the model
    content_model = "You are an assistant classifying images into user defined categories."
    prompt = (
        f"Given the following categories:\n"
        f"{categories_context}\n\n"
        "Determine which category the following image belongs to and why:"
    )

    response = openai.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": content_model
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=100,
        response_format=CategoryDecisionReasoning,
    )

    # Extract the model's response
    category_name = response.choices[0].message.parsed.category.value
    category_reasoning = response.choices[0].message.parsed.reasoning
    print(f'Classified {image_name} as: {category_name}')
    print(f'Classified because:\n{category_reasoning}')

    # Step 6: Check if the response is a valid category
    valid_category = next((cat for cat in categories if cat["category"] == category_name), None)
    print(f'is valid category? {valid_category}\n-----')
    
    if valid_category:
        # Step 6.a: Copy image to the appropriate folder
        target_folder = os.path.join(output_folder, valid_category["folder_name"])
        shutil.copy(image_path, target_folder)

        classified_image = {
            "image_name": image_name,
            "category": category_name,
            "reasoning": category_reasoning
        }
    else:
        # Step 6.b: Copy image to the "failed" folder
        category_name = 'failed'
        category_reasoning = None
        shutil.copy(image_path, failed_folder)
        
        classified_image = {
            "image_name": image_name,
            "category": category_name,
            "reasoning": category_reasoning
        }

    output_json.append(classified_image)

timestamp_ = timestamp()

# document the image classifications
with open(f'image_classifications_{timestamp_}.json', 'w') as f:
    json.dump(output_json, f, indent=4)


print("Image classification completed.")
