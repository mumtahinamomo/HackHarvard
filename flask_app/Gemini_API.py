import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Create a datetime object for today
today = datetime.today()

# Convert to string
today_str = today.strftime("%Y-%m-%d %H:%M:%S")
print(today_str)


genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-pro-latest")

def describe_politician(name):
    prompt = f"Provide short description of the politician {name}, including their background, political career, and notable policies."
    response = model.generate_content(prompt)
    return response.text

#print(describe_politician("Kamala Harris"))

def upcoming_elections(location,today=today_str):
    
    prompt = f"Give a comprehensive list of all elections within 10 miles radius of {location} ocurring up until 6 months after {today_str}. Please list only the date of the election and what the election is for"
    response = model.generate_content(prompt)
    return response.text
print(upcoming_elections("waltham"))