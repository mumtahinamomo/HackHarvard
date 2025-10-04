from flask import redirect, render_template, request, jsonify, url_for
import pandas as pd
from fuzzywuzzy import process
import csv

from . import app
from .models import Politician

@app.route('/politician/<string:politician_id>')
def politician(politician_id):
    print(politician_id)
    politician = Politician.query.filter_by(candidate_id=politician_id).first()
    print(politician)
    return render_template('politician.html', politician = politician)

@app.route('/search', methods=['POST'])
def search():
    search_term = request.form['search']
    return redirect(url_for('search_results', search_term = search_term))

@app.route('/search/<string:search_term>')
def search_results(search_term: str):
    matches = fuzzy_search_politicians(search_term, limit=20)
    return render_template('search_results.html', search_term=search_term, search_results=matches)

def format_name_for_search(name):
    """Convert 'LAST, FIRST' format to 'FIRST LAST' format."""
    if ',' in name:
        parts = name.split(',', 1)  # Split only on first comma
        if len(parts) == 2:
            last_name = parts[0].strip()
            first_name = parts[1].strip()
            return f"{first_name} {last_name}"
    return name.strip()

def fuzzy_search_politicians(search_term, limit=20):
    """
    Perform fuzzy search on politician names in the database.
    Returns top matches with their IDs and scores.
    """
    # Get all politicians from the database
    politicians = Politician.query.all()
    
    if not politicians:
        return []
    
    # Create a dictionary mapping formatted names to politician objects
    # name_to_politician = {}
    politician_id_to_name = {}
    for politician in politicians:
        # Convert "LAST, FIRST" to "FIRST LAST" for better matching
        formatted_name = format_name_for_search(politician.candidate_name)
        politician_id_to_name[politician.candidate_id] = formatted_name
        # name_to_politician[formatted_name] = politician
    
    # Perform fuzzy matching
    matches = process.extract(search_term, politician_id_to_name, limit=limit)

    politician_results = []

    for match in matches:
        politician = Politician.query.filter_by(candidate_id=match[2]).first()
        politician_results.append((politician, match[1]))

    # return politician_results
    results = []
    for politician, score in politician_results:
        results.append({
            'id': politician.id,
            'candidate_id': politician.candidate_id,
            'candidate_name': politician.candidate_name,
            'formatted_name': politician_id_to_name[politician.candidate_id],
            'chamber': politician.chamber,
            'political_party_affiliation': politician.political_party_affiliation,
            'office_state': politician.office_state,
            'office_district': politician.office_district,
            'score': score
        })
    return results