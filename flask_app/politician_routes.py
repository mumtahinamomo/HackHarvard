from flask import render_template
import csv

from . import app

@app.route('/politician/<string:politician_id>')
def politician(politician_id):
    print(politician_id)
    data = get_politician_data(politician_id)
    print(data)
    return render_template('politician.html', data = data)

def get_politician_data(politician_id):
    # Get data from the csv files
    filenames = ['flask_app/data/house_candidates.csv', 'flask_app/data/senate_candidates.csv']
    for filename in filenames:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == politician_id:
                    return row
    return None