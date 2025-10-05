from flask import redirect, render_template, request, jsonify, url_for
import pandas as pd
from fuzzywuzzy import process
import csv
from datetime import datetime
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
    # if politician and not politician.description:
        
    #     try:
    #         description = describe_politician(politician.candidate_name, politician.website_url)
    #         politician.description = description
    #         db.session.commit()
    #     except Exception as e:
    #         print(f"Error generating description for {politician.candidate_name}: {e}")
    #         # Set a default description if Gemini API fails
    #         politician.description = f"{politician.candidate_name} is a {politician.political_party_affiliation} politician representing {politician.office_state}."
    #         db.session.commit()
    
    return render_template('politician.html', politician = politician)

@app.route('/generate_description/<string:politician_id>')
def generate_description(politician_id):
    try:
        politician = Politician.query.filter_by(candidate_id=politician_id).first()
        if not politician:
            return jsonify({'error': 'Politician not found'}), 404
        
        # Generate description using Gemini API
        description = describe_politician(politician.candidate_name, politician.website_url)
        
        # Save description to database
        politician.description = description
        politician.description_generated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'description': description,
            'generated_at': politician.description_generated_at
        })
        
    except Exception as e:
        print(f"Error generating description for {politician_id}: {e}")
        return jsonify({'error': 'Failed to generate description'}), 500

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
    
    # Get chambers with counts
    chamber_counts = db.session.query(
        Politician.chamber,
        func.count(Politician.id).label('count')
    ).filter(
        Politician.chamber.isnot(None)
    ).group_by(
        Politician.chamber
    ).order_by(
        func.count(Politician.id).desc()
    ).all()
    
    all_chambers = [chamber[0] for chamber in chamber_counts]
    
    # Get states with counts
    state_counts = db.session.query(
        Politician.office_state,
        func.count(Politician.id).label('count')
    ).filter(
        Politician.office_state.isnot(None),
        Politician.office_state != '00'
    ).group_by(
        Politician.office_state
    ).order_by(
        func.count(Politician.id).desc()
    ).all()
    
    all_states = [state[0] for state in state_counts]
    
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
                         all_chambers=all_chambers,
                         all_states=all_states,
                         all_parties=all_parties,
                         chamber_counts=chamber_counts,
                         state_counts=state_counts,
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
    
    # Get live counts for each filter category (based on current search + other filters)
    # Chamber counts (excluding chamber filter to show remaining options)
    chamber_query = Politician.query
    if search_term:
        chamber_query = chamber_query.filter(Politician.candidate_name.ilike(f'%{search_term}%'))
    if states:
        chamber_query = chamber_query.filter(Politician.office_state.in_(states))
    if parties:
        chamber_query = chamber_query.filter(Politician.political_party_affiliation.in_(parties))
    
    chamber_counts = chamber_query.filter(
        Politician.chamber.isnot(None)
    ).with_entities(
        Politician.chamber,
        func.count(Politician.id).label('count')
    ).group_by(
        Politician.chamber
    ).order_by(
        func.count(Politician.id).desc()
    ).all()
    
    # State counts (excluding state filter to show remaining options)
    state_query = Politician.query
    if search_term:
        state_query = state_query.filter(Politician.candidate_name.ilike(f'%{search_term}%'))
    if chambers:
        state_query = state_query.filter(Politician.chamber.in_(chambers))
    if parties:
        state_query = state_query.filter(Politician.political_party_affiliation.in_(parties))
    
    state_counts = state_query.filter(
        Politician.office_state.isnot(None),
        Politician.office_state != '00'
    ).with_entities(
        Politician.office_state,
        func.count(Politician.id).label('count')
    ).group_by(
        Politician.office_state
    ).order_by(
        func.count(Politician.id).desc()
    ).all()
    
    # Party counts (excluding party filter to show remaining options)
    party_query = Politician.query
    if search_term:
        party_query = party_query.filter(Politician.candidate_name.ilike(f'%{search_term}%'))
    if chambers:
        party_query = party_query.filter(Politician.chamber.in_(chambers))
    if states:
        party_query = party_query.filter(Politician.office_state.in_(states))
    
    party_counts = party_query.filter(
        Politician.political_party_affiliation.isnot(None)
    ).with_entities(
        Politician.political_party_affiliation,
        func.count(Politician.id).label('count')
    ).group_by(
        Politician.political_party_affiliation
    ).order_by(
        func.count(Politician.id).desc()
    ).all()
    
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
        'total_pages': (total_count + per_page - 1) // per_page,
        'chamber_counts': [{'chamber': c[0], 'count': c[1]} for c in chamber_counts],
        'state_counts': [{'state': s[0], 'count': s[1]} for s in state_counts],
        'party_counts': [{'party': p[0], 'count': p[1]} for p in party_counts]
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

@app.route('/network')
def network_viewer():
    """Serve the working OpenBallot network visualization."""
    import os
    demo_path = os.path.join(os.path.dirname(__file__), 'graph', 'openballot_server', 'demo.html')
    if os.path.exists(demo_path):
        with open(demo_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    else:
        return "Network visualization not found", 404
