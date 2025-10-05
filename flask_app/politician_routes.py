from flask import redirect, render_template, request, jsonify, url_for
import pandas as pd
from fuzzywuzzy import process
import csv
from sqlalchemy import func

from . import app, db
from .models import Politician
from .Gemini_API import describe_politician

@app.route('/politician/<string:politician_id>')
def politician(politician_id):
    print(politician_id)
    politician = Politician.query.filter_by(candidate_id=politician_id).first()
    print(politician)
    
    # Generate description if it doesn't exist
    if politician and not politician.description:
        try:
            description = describe_politician(politician.candidate_name, politician.website_url)
            politician.description = description
            db.session.commit()
        except Exception as e:
            print(f"Error generating description for {politician.candidate_name}: {e}")
            # Set a default description if Gemini API fails
            politician.description = f"{politician.candidate_name} is a {politician.political_party_affiliation} politician representing {politician.office_state}."
            db.session.commit()
    
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
    
    politician_id_to_name = {}
    for politician in politicians:
        # Convert "LAST, FIRST" to "FIRST LAST" for better matching
        formatted_name = format_name_for_search(politician.candidate_name)
        politician_id_to_name[politician.candidate_id] = formatted_name
    
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

@app.route('/list_politicians')
def list_politicians():
    # Get query parameters for filtering
    search_term = request.args.get('search', '').strip()
    chambers = request.args.getlist('chamber')
    states = request.args.getlist('state')
    parties = request.args.getlist('party')
    
    # Start with base query
    query = Politician.query
    
    # Apply search filter
    if search_term:
        query = query.filter(Politician.candidate_name.ilike(f'%{search_term}%'))
    
    # Apply chamber filter
    if chambers:
        query = query.filter(Politician.chamber.in_(chambers))
    
    # Apply state filter
    if states:
        query = query.filter(Politician.office_state.in_(states))
    
    # Apply party filter
    if parties:
        query = query.filter(Politician.political_party_affiliation.in_(parties))
    
    politicians = query.all()
    
    # Get unique values for filter options
    all_chambers = [p.chamber for p in Politician.query.with_entities(Politician.chamber).distinct().all() if p.chamber]
    all_states = [p.office_state for p in Politician.query.with_entities(Politician.office_state).distinct().all() if p.office_state and p.office_state != '00']
    
    # Get parties sorted by number of candidates (most to least)
    party_counts = db.session.query(
        Politician.political_party_affiliation,
        func.count(Politician.id).label('count')
    ).filter(
        Politician.political_party_affiliation.isnot(None)
    ).group_by(
        Politician.political_party_affiliation
    ).order_by(
        func.count(Politician.id).desc()
    ).all()
    
    all_parties = [party[0] for party in party_counts]
    
    return render_template('list_politicians.html', 
                         politicians=politicians,
                         search_term=search_term,
                         selected_chambers=chambers,
                         selected_states=states,
                         selected_parties=parties,
                         all_chambers=sorted(all_chambers),
                         all_states=sorted(all_states),
                         all_parties=all_parties,
                         party_counts=party_counts)

@app.route('/api/politicians')
def api_politicians():
    """API endpoint for live search and filtering"""
    # Get query parameters for filtering
    search_term = request.args.get('search', '').strip()
    chambers = request.args.getlist('chamber')
    states = request.args.getlist('state')
    parties = request.args.getlist('party')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    
    # Start with base query
    query = Politician.query
    
    # Apply search filter
    if search_term:
        query = query.filter(Politician.candidate_name.ilike(f'%{search_term}%'))
    
    # Apply chamber filter
    if chambers:
        query = query.filter(Politician.chamber.in_(chambers))
    
    # Apply state filter
    if states:
        query = query.filter(Politician.office_state.in_(states))
    
    # Apply party filter
    if parties:
        query = query.filter(Politician.political_party_affiliation.in_(parties))
    
    # Get total count for pagination
    total_count = query.count()
    
    # Apply pagination
    politicians = query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Convert to JSON-serializable format
    results = []
    for p in politicians:
        results.append({
            'id': p.id,
            'candidate_id': p.candidate_id,
            'candidate_name': p.candidate_name,
            'chamber': p.chamber,
            'political_party_affiliation': p.political_party_affiliation,
            'office_state': p.office_state,
            'office_district': p.office_district,
            'total_receipts': p.total_receipts,
            'website_url': p.website_url
        })
    
    return jsonify({
        'politicians': results,
        'total_count': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_count + per_page - 1) // per_page
    })

@app.route('/admin/clear-cache')
def clear_description_cache():
    """Admin route to clear all politician description cache."""
    try:
        # Update all politicians to have None descriptions
        Politician.query.update({Politician.description: None})
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Successfully cleared descriptions for {Politician.query.count()} politicians'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/graph')
def graph_viewer():
    """Graph viewer page without specific politician."""
    return render_template('graph_viewer.html')

@app.route('/graph/<string:politician_id>')
def graph_viewer_politician(politician_id):
    """Graph viewer page for specific politician."""
    politician = Politician.query.filter_by(candidate_id=politician_id).first()
    return render_template('graph_viewer.html', politician=politician)
