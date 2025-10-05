#!/usr/bin/env python3
"""
Cache clearing script for politician descriptions.
This script clears all cached descriptions from the database after a push.
"""

import os
import sys
sys.path.append('/Users/jacob/Desktop/Hackathon/Hackathon final stand/HackHarvard')

from flask_app import app, db
from flask_app.models import Politician

def clear_description_cache():
    """Clear all cached politician descriptions from the database."""
    with app.app_context():
        try:
            # Update all politicians to have None descriptions
            Politician.query.update({Politician.description: None})
            db.session.commit()
            print("✅ Successfully cleared all politician description cache!")
            print(f"Cleared descriptions for {Politician.query.count()} politicians")
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
            db.session.rollback()

if __name__ == "__main__":
    clear_description_cache()
