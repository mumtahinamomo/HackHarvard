#!/usr/bin/env python3
"""
Script to populate the database with candidate data from CSV files.
This is a one-time script to load the new_data CSV files into the database.
"""

import csv
import os
import sys
from pathlib import Path
from fuzzywuzzy import process

# Add the flask_app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'flask_app'))

from flask_app import app, db
from flask_app.models import Politician

def safe_float(value):
    """Convert string to float, handling empty strings and invalid values."""
    if not value or value.strip() == '':
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def safe_string(value):
    """Convert value to string, handling None and empty values."""
    if value is None:
        return ''
    return str(value).strip()

def get_chamber_from_candidate_id(candidate_id):
    """Determine chamber (House/Senate) from candidate ID."""
    if candidate_id.startswith('H'):
        return 'House'
    elif candidate_id.startswith('S'):
        return 'Senate'
    else:
        return 'Unknown'

def populate_from_csv(csv_file_path, chamber):
    """Populate database from a single CSV file."""
    print(f"Processing {chamber} data from: {csv_file_path}")
    
    if not os.path.exists(csv_file_path):
        print(f"Error: File not found: {csv_file_path}")
        return 0
    
    count = 0
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            try:
                # Create new Politician record
                politician = Politician(
                    candidate_id=safe_string(row['CAND_ID']),
                    candidate_name=safe_string(row['CAND_NAME']),
                    chamber=chamber,
                    website_url = None,
                    incumbent_challenger_indicator=safe_string(row['CAND_ICI']),
                    political_party_affiliation=safe_string(row['CAND_PTY_AFFILIATION']),
                    total_receipts=safe_float(row['TTL_RECEIPTS']),
                    debts_owed_by=safe_float(row['DEBTS_OWED_BY']),
                    total_individual_contributions=safe_float(row['TTL_INDIV_CONTRIB']),
                    office_state=safe_string(row['CAND_OFFICE_ST']),
                    office_district=safe_string(row['CAND_OFFICE_DISTRICT']),
                    other_political_committee_contributions=safe_float(row['OTHER_POL_CMTE_CONTRIB']),
                    political_party_contributions=safe_float(row['POL_PTY_CONTRIB']),
                    coverage_end_date=safe_string(row['CVG_END_DT']),
                    individual_refunds=safe_float(row['INDIV_REFUNDS']),
                    committee_refunds=safe_float(row['CMTE_REFUNDS']),
                    percent_individual_contributions=safe_float(row['PCT_INDIV_CONTRIB']),
                    pac_contribution_percentage=safe_float(row.get('PAC_Contribution_%', 0.0)),
                    party_contribution_percentage=safe_float(row.get('Party_Contribution_%', 0.0)),
                    adjusted_party_contributions=safe_float(row.get('Adj_Party_Contrib', 0.0)),
                    adjusted_pac_contributions=safe_float(row.get('Adj_PAC_Contrib', 0.0)),
                    percent_individual=safe_float(row.get('Pct_Individual', 0.0)) or safe_float(row.get('PCT_FROM_INDIV', 0.0)),
                    funding_group=safe_string(row.get('Funding_Group', '')),
                    individual_percentile_all=safe_float(row.get('Individual_Pctile_All', 0.0)),
                    individual_percentile_bin=safe_string(row.get('Individual_Pctile_Bin', ''))
                )
                
                db.session.add(politician)
                count += 1
                
                # Commit every 100 records to avoid memory issues
                if count % 100 == 0:
                    db.session.commit()
                    print(f"Processed {count} {chamber} records...")
                    
            except Exception as e:
                print(f"Error processing row {count + 1}: {e}")
                print(f"Row data: {row}")
                continue
    
    # Commit any remaining records
    db.session.commit()
    print(f"Completed processing {count} {chamber} records")
    return count

def main1():
    """Main function to populate the database."""
    print("Starting database population...")
    
    # Get the base directory
    base_dir = Path(__file__).parent
    new_data_dir = base_dir / 'flask_app' / 'new_data'
    
    # Check if new_data directory exists
    if not new_data_dir.exists():
        print(f"Error: new_data directory not found at {new_data_dir}")
        return
    
    # Initialize database within Flask app context
    with app.app_context():
        # Clear existing data (optional - remove if you want to keep existing data)
        print("Clearing existing Politician records...")
        Politician.query.delete()
        db.session.commit()
        
        # Process House data
        house_csv = new_data_dir / 'house_candidates_indiv_percentiles.csv'
        house_count = populate_from_csv(house_csv, 'House')
        
        # Process Senate data
        senate_csv = new_data_dir / 'senate_candidates_indiv_percentiles.csv'
        senate_count = populate_from_csv(senate_csv, 'Senate')

        #Process President data
        president_csv = new_data_dir / 'president_data.csv'
        president_count = populate_from_csv(president_csv, 'President')
        
        total_count = president_count
        print(f"\nDatabase population complete!")
        print(f"Total records added: {total_count}")
        print(f"  - President: {president_count}")
        print(f"  - House: {house_count}")
        print(f"  - Senate: {senate_count}")

def main2():
    """Main function to populate the database."""
    print("Starting database population...")
    

    # Get the base directory
    base_dir = Path(__file__).parent
    new_data_dir = base_dir / 'flask_app' / 'data'
    
    # Check if new_data directory exists
    if not new_data_dir.exists():
        print(f"Error: new_data directory not found at {new_data_dir}")
        return
    
    # Initialize database within Flask app context
    with app.app_context():
        # Clear existing data (optional - remove if you want to keep existing data)
        # print("Clearing existing Politician records...")
        # Politician.query.delete()
        # db.session.commit()
        
        # Process House data
        house_csv = new_data_dir / 'house_websites.csv'
        house_count = populate_website_urls_from_csv(house_csv, 'House')
        
        # Process Senate data
        senate_csv = new_data_dir / 'senate_websites.csv'
        senate_count = populate_website_urls_from_csv(senate_csv, 'Senate')
        
        total_count = senate_count
        print(f"\nDatabase population complete!")
        print(f"Total records added: {total_count}")
        print(f"  - House: {house_count}")
        print(f"  - Senate: {senate_count}")


def populate_website_urls_from_csv(csv_file_path, chamber):
    """Populate database from a single CSV file."""
    print(f"Processing {chamber} data from: {csv_file_path}")
    
    if not os.path.exists(csv_file_path):
        print(f"Error: File not found: {csv_file_path}")
        return 0
    
    count = 0
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # try:
                
            website_url = safe_string(row['Website'])
            name = safe_string(row['Name'])
            matched_name = safe_string(row['Matched Name'])

            # state_politicians = Politician.query.filter_by(office_state=state_abbr).all()
            
            # politician_id_to_name = {}
            # for politician in state_politicians:
            #     # Convert "LAST, FIRST" to "FIRST LAST" for better matching
            #     formatted_name = format_name_for_search(politician.candidate_name)
            #     politician_id_to_name[politician.candidate_id] = formatted_name

            # # Perform fuzzy matching
            # matches = process.extract(name, politician_id_to_name, limit=3)

            # # politician_results = []

            # # for match in matches:
            # #     politician = Politician.query.filter_by(candidate_id=match[2]).first()
            # #     politician_results.append((politician.candidate_name, match[1]))


            # correct_politician_name = matches[0][0]

            # if (matches[0][1] < 85) or ((matches[0][1] - matches[1][1]) < 11):
            #     print("\nMatches:")
            #     print(f"{name} - {website_url}")
            #     for i, match in enumerate(matches):
            #         print(f"{i+1}. {match[0]} - {match[1]}")
            #     selection = input("\nSelect the correct politician (1, 2, or 3): ")
            #     if selection == '1':
            #         correct_politician_name = matches[0][0]
            #     elif selection == '2':
            #         correct_politician_name = matches[1][0]
            #     elif selection == '3':
            #         correct_politician_name = matches[2][0]
            #     else: correct_politician_name = Politician.query.filter_by(candidate_id=selection).first().candidate_name


            # print(f"{name}, {correct_politician_name}")
            correct_politicians: list[Politician] = Politician.query.filter_by(candidate_name=matched_name).all()
            for politician in correct_politicians:
                politician.website_url = website_url
                db.session.add(politician)
            # db.session.commit()
            # print(correct_politicians)
            # print(matches[0][1], correct_politicians[0].candidate_name)


            # db.session.add(politician)
            count += 1
            
            # Commit every 100 records to avoid memory issues
            if count % 100 == 0:
                db.session.commit()
                print(f"Processed {count} {chamber} records...")
                    
            # except Exception as e:
            #     print(f"Error processing row {count + 1}: {e}")
            #     print(f"Row data: {row}")
            #     continue
    
    # Commit any remaining records
    db.session.commit()
    print(f"Completed processing {count} {chamber} records")
    return count

def format_name_for_search(name):
    """Convert 'LAST, FIRST' format to 'FIRST LAST' format."""
    if ',' in name:
        parts = name.split(',', 1)  # Split only on first comma
        if len(parts) == 2:
            last_name = parts[0].strip()
            first_name = parts[1].strip()
            return f"{first_name} {last_name}"
    return name.strip()

if __name__ == '__main__':
    # main1()
    main2()