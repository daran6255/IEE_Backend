from flask import Flask, render_template, send_file
import json
import pandas as pd
import os

# template_dir = os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
app = Flask(__name__, static_folder='frontend/static', template_folder='frontend/templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download_excel')
def download_excel():
    # Create sample Excel data (you can replace this with your data)
    data = {'Name': ['John', 'Anna', 'Peter', 'Linda'],
            'Age': [28, 35, 42, 25],
            'City': ['New York', 'Paris', 'Berlin', 'London']}
    df = pd.DataFrame(data)

    # Save DataFrame to Excel file
    excel_file = 'data.xlsx'
    df.to_excel(excel_file, index=False)

    return send_file(excel_file, as_attachment=True)

@app.route('/download_json')
def download_json():
    # Create sample JSON data (you can replace this with your data)
    data = {'Name': ['John', 'Anna', 'Peter', 'Linda'],
            'Age': [28, 35, 42, 25],
            'City': ['New York', 'Paris', 'Berlin', 'London']}
    json_data = json.dumps(data)

    # Save JSON data to file
    json_file = 'data.json'
    with open(json_file, 'w') as file:
        file.write(json_data)

    return send_file(json_file, as_attachment=True)

# @app.route('/extract_data')

if __name__ == '__main__':
    app.run(debug=True)
