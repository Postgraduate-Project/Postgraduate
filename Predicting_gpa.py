#########################################################################
# Title  : Predicting GPA of students using the best model
# Author : Kevin Ryan Noronha
# Editor : Disha Khurana – Updated 4 June 2025 – Using only HGBR model, Added download for failing students and bar chart
#########################################################################

# Importing necessary libraries 
import os
import io
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import base64
import joblib
from flask import (
    Blueprint, render_template,
    request, redirect, flash,
    send_file
)

ml_bp = Blueprint('ml', __name__, template_folder='templates')

# ─── Path to the best model ───
BASE_DIR  = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, 'Machine Learning')
HIST_PATH = os.path.join(MODEL_DIR, 'gpa_hist_model_cp.pkl')

# ─── Loading model and metadata ───
hist_store   = joblib.load(HIST_PATH)
model_hist   = hist_store['model']
subject_cols = [c for c in hist_store['subject_cols'] if c != 'GPA']

# ─── GPA Range Formatter ───
def gpa_range(val):
    if val < 1.5:
        return "0.0 – 1.5"
    elif val < 2.0:
        return "1.5 – 2.0"
    elif val < 2.5:
        return "2.0 – 2.5"
    elif val < 3.0:
        return "2.5 – 3.0"
    elif val < 3.5:
        return "3.0 – 3.5"
    else:
        return "3.5 – 4.0"

# ─── Preprocessing  uploaded student data ───
def preprocess_input(df: pd.DataFrame) -> pd.DataFrame:
    df = df[['Emplid', 'Name', 'Course', 'Mark']].drop_duplicates()
    df['Emplid'] = df['Emplid'].astype(str)
    df['Mark'] = pd.to_numeric(df['Mark'], errors='coerce')
    df['Mark'].fillna(df['Mark'].median(), inplace=True)

    pivot = (
        df
        .pivot_table(
            index=['Emplid', 'Name'],
            columns='Course',
            values='Mark',
            aggfunc='first'
        )
        .reset_index()
    )

    # Normalizing each subject column based on its column mean
    data = pivot.copy()
    for col in subject_cols:
        mu = data[col].dropna().mean()
        data[col].fillna(mu, inplace=True)
        data[col] = (data[col] - mu) / mu

    return data

# ─── Flask Route for GPA Prediction ───
@ml_bp.route('/', methods=['GET', 'POST'])
def home():
    table_html = None
    results = None
    chart_base64 = None

    if request.method == 'POST':
        f = request.files.get('datafile')
        if not f or not f.filename:
            flash("Please upload a CSV or Excel file.")
            return redirect(request.url)

        ext = f.filename.rsplit('.', 1)[1].lower()
        try:
            df_raw = pd.read_excel(f) if ext in ('xls', 'xlsx') else pd.read_csv(f)
        except Exception:
            flash("Could not read file. Make sure it's valid CSV/XLS/XLSX.")
            return redirect(request.url)

        # Preprocessing input
        data = preprocess_input(df_raw)

        # Removing empty 'Course' column 
        data = data.drop(columns=[col for col in data.columns if col.lower() == 'course'], errors='ignore')

        X_new = data[subject_cols]

        # Predicting GPA using the best model
        pred_hist = model_hist.predict(X_new)

        # Formatting predictions
        results = data[['Emplid', 'Name']].copy()
        results['Estimated GPA Range'] = [gpa_range(p) for p in pred_hist]
        results['Predicted GPA'] = [round(p, 3) for p in pred_hist]

        # Generating bar chart of pass vs fail
        try:
            count_pass = sum(pred_hist >= 2.0)
            count_fail = sum(pred_hist < 2.0)
            labels = ['Eligible GPA', 'At-Risk GPA']
            counts = [count_pass, count_fail]

            fig, ax = plt.subplots()
            ax.bar(labels, counts, color=['#161E87', '#A61C30'])
            ax.set_ylabel('Number of Students')
            ax.set_title('Students by GPA Category')

            img_buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(img_buf, format='png', dpi=150)
            img_buf.seek(0)
            chart_base64 = base64.b64encode(img_buf.getvalue()).decode('utf-8')
            plt.close(fig)
        except Exception as e:
            print("Chart generation failed:", e)

        # Converting to HTML table
        table_html = results.to_html(
            index=False,
            classes='table table-bordered data-table',
            table_id='ml-table',
            escape=False
        )

    return render_template('machine_learning.html', table_html=table_html, results=results, chart_base64=chart_base64)

# ─── Route for Downloading Failing Students ───
@ml_bp.route('/download-failures', methods=['POST'])
def download_failures():
    try:
        failing_json = request.form.get("failing_data")
        df = pd.read_json(failing_json)

        output = io.BytesIO()
        df.to_excel(output, index=False, sheet_name="Failing Students")
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name="failing_students.xlsx"
        )
    except Exception as e:
        flash(f"Download failed: {str(e)}")
        return redirect('/')
