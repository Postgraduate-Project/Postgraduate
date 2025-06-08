#########################################################################
#Title  : Predicting GPA of students using different models
#Author : Kevin Ryan Noronha

#Editors: Please Enter your Name/Date and description of the edit below 




##########################################################################

import os
import pandas as pd
import joblib
from flask import (
    Blueprint, render_template,
    request, redirect, flash,
    current_app
)

ml_bp = Blueprint('ml', __name__, template_folder='templates')

# ─── Paths to your three models ───
BASE_DIR    = os.path.dirname(__file__)
HIST_PATH   = os.path.join(BASE_DIR, 'gpa_hist_model_cp.pkl')
KNN_PATH    = os.path.join(BASE_DIR, 'gpa_knnreg_model.pkl')
RF_PATH     = os.path.join(BASE_DIR, 'gpa_reg_model.pkl')

# ─── Load HistGBR store for subject_cols + model ───
hist_store      = joblib.load(HIST_PATH)
model_hist      = hist_store['model']
subject_cols    = [c for c in hist_store['subject_cols'] if c != 'GPA']

# ─── Load KNN regressor ───
knn_store       = joblib.load(KNN_PATH)
model_knn       = knn_store.get('model', knn_store) if isinstance(knn_store, dict) else knn_store

# ─── Load RandomForest regressor ───
rf_store        = joblib.load(RF_PATH)
model_rf        = rf_store.get('model', rf_store) if isinstance(rf_store, dict) else rf_store


def preprocess_input(df: pd.DataFrame) -> pd.DataFrame:
    # keep only the necessary cols
    df = df[['Emplid','Name','Course','Mark']].drop_duplicates()
    df['Emplid'] = df['Emplid'].astype(str)
    df['Mark'] = pd.to_numeric(df['Mark'], errors='coerce')
    df['Mark'].fillna(df['Mark'].median(), inplace=True)

    # pivot so each course is a column
    pivot = (
        df
        .pivot_table(
            index=['Emplid','Name'],
            columns='Course',
            values='Mark',
            aggfunc='first'
        )
        .reset_index()
    )

    # normalize each subject column
    data = pivot.copy()
    for col in subject_cols:
        mu = data[col].dropna().mean()
        data[col].fillna(mu, inplace=True)
        data[col] = (data[col] - mu) / mu

    return data


@ml_bp.route('/', methods=['GET','POST'])
def home():
    table_html = None

    if request.method == 'POST':
        f = request.files.get('datafile')
        if not f or not f.filename:
            flash("Please upload a CSV or Excel file.")
            return redirect(request.url)

        ext = f.filename.rsplit('.',1)[1].lower()
        try:
            df_raw = pd.read_excel(f) if ext in ('xls','xlsx') else pd.read_csv(f)
        except Exception:
            flash("Could not read file. Make sure it's valid CSV/XLS/XLSX.")
            return redirect(request.url)

        data = preprocess_input(df_raw)
        X_new = data[subject_cols]

        # make predictions
        pred_hist = model_hist.predict(X_new)
        pred_knn  = model_knn.predict(X_new)
        pred_rf   = model_rf.predict(X_new)

        # assemble results
        results = data[['Emplid','Name']].copy()

        #Add the logic of making these lists look like a range for each value here#

        ###########################################################################
        #Mark the 3 lines below to remove them from the data frame
        results['HistGradientBoosting'] = pred_hist
        results['KNN']                  = pred_knn
        results['RandomForest']         = pred_rf

        # render HTML table with same classes & ID
        table_html = results.to_html(
            index=False,
            classes='table table-bordered data-table',
            table_id='ml-table',
            float_format="%.2f",
            escape=False
        )

    return render_template(
        'machine_learning.html',
        table_html=table_html
    )
