#!/usr/bin/env python3
"""
Script to populate the database with candidate data from CSV files.
This is a one-time script to load the new_data CSV files into the database.
"""

import csv
import os
import sys
from pathlib import Path

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
                    pac_contribution_percentage=safe_float(row['PAC_Contribution_%']),
                    party_contribution_percentage=safe_float(row['Party_Contribution_%']),
                    adjusted_party_contributions=safe_float(row['Adj_Party_Contrib']),
                    adjusted_pac_contributions=safe_float(row['Adj_PAC_Contrib']),
                    percent_individual=safe_float(row['Pct_Individual']),
                    funding_group=safe_string(row['Funding_Group']),
                    individual_percentile_all=safe_float(row['Individual_Pctile_All']),
                    individual_percentile_bin=safe_string(row['Individual_Pctile_Bin'])
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

def main():
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
        
        total_count = house_count + senate_count
        print(f"\nDatabase population complete!")
        print(f"Total records added: {total_count}")
        print(f"  - House: {house_count}")
        print(f"  - Senate: {senate_count}")

if __name__ == '__main__':
    main()
