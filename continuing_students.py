#########################################################################
# Title  : Predicting GPA of students using the best model
# Author : Kevin Ryan Noronha
# Editor : Disha Khurana 
# Updated: 1 June 2025 
# Updates: Filtered merged columns, standardized 'Change of Program' values to Y/N, sorted by program name and forename, added beautified headers, enhanced error handling, and included comments for clarity.
#########################################################################

# Importing necessary libraries
import os
import io
import base64
import pandas as pd
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
from flask import Blueprint, render_template, request, redirect, flash, current_app
from werkzeug.utils import secure_filename

# Creating a Flask Blueprint for the 'Continuing Students feature'
continuing_bp = Blueprint('continuing', __name__, template_folder='templates')

# Allowing file extensions for upload
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}

# Checking if uploaded file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Beautifying column names for display
def beautify_column(col):
    overrides = {
        'rmit_student_id': 'RMIT Student ID',
        'application_id': 'Application ID',
        'applicant_id': 'Applicant ID',
        'change_of_program': 'Change of Program',
        'admit_term': 'Admit Term',
        'plan_code': 'Plan Code',
        'plan_name': 'Plan Name',
        'commencement_date': 'Commencement Date',
        'application_status': 'Application Status',
        'fund_source': 'Fund Source'
    }
    return overrides.get(col, ' '.join(word.capitalize() for word in col.replace('_', ' ').split()))

# Main route handling logic
@continuing_bp.route('/', methods=['GET', 'POST'])
def home():
    table_html = None
    chart_base64 = None

    if request.method == 'POST':
        # Get uploaded files
        f1 = request.files.get('file1')
        f2 = request.files.get('file2')

        # Checking if both files are uploaded
        if not f1 or not f2:
            flash('Both files must be uploaded.', 'error')
            return redirect(request.url)

        # Enforcing specific filenames
        if f1.filename != 'current_students.xlsx' or f2.filename != 'future_students.xlsx':
            flash("You must upload files named 'current_students.xlsx' and 'future_students.xlsx' only.", 'error')
            return redirect(request.url)

        # Checking for valid file types
        if not allowed_file(f1.filename) or not allowed_file(f2.filename):
            flash('Invalid file type. Only CSV, XLS, and XLSX are allowed.', 'error')
            return redirect(request.url)

        # Attempting to read both Excel files
        try:
            df1 = pd.read_excel(f1)
            df2 = pd.read_excel(f2)
        except Exception as e:
            flash('Error reading Excel files. Ensure they are not corrupted.', 'error')
            return redirect(request.url)

        # Ensuring required columns are present
        if 'Student No' not in df1.columns or 'application id' not in df2.columns:
            flash("Required columns missing. Sheet 1 must contain 'Student No', and Sheet 2 must contain 'application id'.", 'error')
            return redirect(request.url)

        # Stripping whitespace from column names
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()

        # Renaming critical identifier columns for consistency
        df1.rename(columns={'Student No': 'rmit_student_id'}, inplace=True)
        df2.rename(columns={'application id': 'application_id'}, inplace=True)

        # Revalidating after renaming
        if 'rmit_student_id' not in df1.columns or 'application_id' not in df2.columns:
            flash("Something went wrong while renaming columns. Please check your file format.", 'error')
            return redirect(request.url)

        # Merging datasets on student ID
        merged = pd.merge(df1, df2, how='inner', on='rmit_student_id')

        # Checking if merged result is empty
        if merged.empty:
            flash('No overlapping rows found between the files.', 'error')
            return redirect(request.url)

        # Selecting and ordering only the required columns for display
        cols = [
            'application_id', 'applicant_id', 'rmit_student_id',
            'Currently enrolled program plan', 'Currently enrolled program name',
            'College', 'forename', 'surname', 'change_of_program',
            'admit_term', 'plan_code', 'plan_name', 'campus',
            'commencement_date', 'application_status', 'fund_source'
        ]

        # Building final DataFrame with only required columns
        final_df = merged[cols]
        final_df.columns = [beautify_column(c) for c in final_df.columns]

       # Sorting the final dataframe by 'program name' and 'student forename'
        final_df.sort_values(by=['Currently Enrolled Program Name', 'Forename'], inplace=True)

        # Replacing NaN with 'N' in 'Change of Program' for clean display
        if 'Change of Program' in final_df.columns:
            final_df['Change of Program'] = final_df['Change of Program'].fillna('N')

        # Generating chart visualising continuing vs non-continuing students
        try:
            ids_1 = set(df1['rmit_student_id'].astype(str).str.strip())
            ids_2 = set(df2['rmit_student_id'].astype(str).str.strip())
            common_ids = ids_1.intersection(ids_2)

            count_cont = len(common_ids)
            count_all_unique = len(ids_1.union(ids_2))
            count_non_cont = count_all_unique - count_cont

            sizes = [count_cont, count_non_cont]
            labels = [f'Continuing ({count_cont})', f'Non-Continuing ({count_non_cont})']
            colors = ['#161E87', '#A61C30']

            fig, ax = plt.subplots(figsize=(6, 6))
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                colors=colors,
                autopct='%1.1f%%',
                startangle=90,
                pctdistance=0.75,
                labeldistance=1.1,
                textprops={'fontsize': 12, 'color': 'white', 'weight': 'bold'}
            )

            # Adding center circle for donut effect
            centre_circle = plt.Circle((0, 0), 0.55, fc='white')
            fig.gca().add_artist(centre_circle)

            # Adding percentage annotation inside the donut
            pct_cont = (count_cont / (count_cont + count_non_cont)) * 100 if (count_cont + count_non_cont) > 0 else 0
            ax.text(0, 0, f'{pct_cont:.0f}%\nContinuing',
                    ha='center', va='center',
                    fontsize=16, color='black', weight='bold')

            ax.axis('equal')  # Ensuring circular pie

            # Converting chart to base64 string for HTML rendering
            img_buf = io.BytesIO()
            plt.savefig(img_buf, format='png', bbox_inches='tight', pad_inches=0.1, dpi=200)
            img_buf.seek(0)
            chart_base64 = base64.b64encode(img_buf.getvalue()).decode('utf-8')
            plt.close(fig)
        except Exception as e:
            print("Chart error:", e)

        # Rendering final table as HTML with DataTables class
        table_html = final_df.to_html(index=False, classes='table table-bordered nowrap', table_id='continuing-table')

        # Cleaning up uploaded files after processing
        try:
            upload_folder = current_app.config.get('UPLOAD_FOLDER')
            p1 = os.path.join(upload_folder, 'current_students.xlsx')
            p2 = os.path.join(upload_folder, 'future_students.xlsx')
            if os.path.exists(p1):
                os.remove(p1)
            if os.path.exists(p2):
                os.remove(p2)
        except Exception as e:
            print(f"File deletion error: {e}")

    # Rendering the output page with table and chart
    return render_template('continuing_students.html', table_html=table_html, chart_base64=chart_base64)
