#!/usr/bin/env python3
"""
Test script to verify the description functionality works correctly.
This script will:
1. Connect to the database
2. Find a politician without a description
3. Generate a description using Gemini API
4. Save it to the database
"""

import os
import sys
sys.path.append('/Users/jacob/Desktop/Hackathon/Hackathon final stand/HackHarvard')

from flask_app import app, db
from flask_app.models import Politician
from flask_app.Gemini_API import describe_politician

def test_description_generation():
    with app.app_context():
        # Find a politician without a description
        politician = Politician.query.filter_by(description=None).first()
        
        if not politician:
            print("No politicians found without descriptions")
            return
        
        print(f"Testing with politician: {politician.candidate_name}")
        print(f"Website URL: {politician.website_url}")
        
        try:
            # Generate description
            description = describe_politician(politician.candidate_name, politician.website_url)
            print(f"Generated description: {description}")
            
            # Save to database
            politician.description = description
            db.session.commit()
            print("Description saved successfully!")
            
        except Exception as e:
            print(f"Error generating description: {e}")

if __name__ == "__main__":
    test_description_generation()
