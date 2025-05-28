# import the necessary libraries
from openai import OpenAI
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from os.path import join, dirname, realpath
from datetime import datetime #datetime
import base64


# path to the directory where the images will be saved
PATH_IMAGES = 'static/uploads/'
FULL_UPLOAD_FOLDER = join(dirname(realpath(__file__)), PATH_IMAGES) #path for saving file

# change the API key to your own
OPENROUTER_API_KEY = "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"

# open router client
openrouter_client = OpenAI(
  base_url="https://openrouter.ai/api/v1", # OpenRouter API URL
  api_key=OPENROUTER_API_KEY, # OpenRouter API Key
)

# change the API key to your own
GEMINI_API_KEY = "AIzaSyDCSYw0heouj41SPRh6chDsJcKhrn9EdMg"

# Initialize the client with your API key
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# function to save image
def save_image(image):
    """
    Save image to file
    :param image: The image to save
    :return: None
    """
    generated_datetime = datetime.now().strftime('%Y%m%d%H%M%S%f')
    filename = generated_datetime+"_googleai_generated.png"

    # save the image to file
    image.save(FULL_UPLOAD_FOLDER+filename)
    
    # return the filename
    return filename

# function to convert image to base64
def image_to_base64(image_path):
    # Open the image file
    with Image.open(image_path) as img:
        # Create a BytesIO object to hold the image data
        buffered = BytesIO()
        # Save the image to the BytesIO object in a specific format (e.g., PNG)
        img.save(buffered, format="jpeg")
        # Get the byte data from the BytesIO object
        img_byte = buffered.getvalue()
        # Encode the byte data to base64
        img_base64 = base64.b64encode(img_byte).decode('utf-8')
    return img_base64

# 1. create function to generate text using Google Gemini AI
def generate_text_gemini(prompt):
    """
    Generate text using Google Gemini AI
    :param prompt: The prompt to generate text from
    :return: The generated text
    """
    
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    # return the generated text
    return response.text