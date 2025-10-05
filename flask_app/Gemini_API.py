import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
import os
import time

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Create a datetime object for today
today = datetime.today()

# Convert to string
today_str = today.strftime("%Y-%m-%d %H:%M:%S")
print(today_str)


genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-pro-latest")

def describe_politician(name, website_url=None):
    if website_url:
        prompt = f"""Provide a 3 bullet point description of the politician {name}, including their background, political career, and notable policies. Use information from their website at {website_url} to provide accurate and up-to-date details about their positions and achievements. 

Return ONLY the HTML code with <ul> and <li> tags. Do not include markdown formatting, code blocks, or any other text. Just the raw HTML."""
    else:
        prompt = f"""Provide a 3 bullet point description of the politician {name}, including their background, political career, and notable policies.

Return ONLY the HTML code with <ul> and <li> tags. Do not include markdown formatting, code blocks, or any other text. Just the raw HTML."""
    
    response = model.generate_content(prompt)
    # Clean up the response to remove any markdown formatting
    text = response.text.strip()
    if text.startswith('```html'):
        text = text[7:]
    if text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    return text.strip()

def upcoming_elections(location,today=today_str):
    
    prompt = f"Give a comprehensive list of all elections within 10 miles radius of {location} ocurring up until 6 months after {today_str}. Please list only the date of the election and what the election is for"
    response = model.generate_content(prompt)
    return response.text

# Comment out the test call to prevent it from running on import
# print(upcoming_elections("waltham"))