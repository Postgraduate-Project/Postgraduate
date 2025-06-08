import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split
import cloudpickle
import os

# --- Load the student dataset ---
df = pd.read_excel("student_records.xlsx")

# --- Prepare the data ---
df = df[['Emplid', 'Name', 'Program Status', 'Course', 'Mark']].drop_duplicates()
df['Emplid'] = df['Emplid'].astype(str)
df['Mark'] = pd.to_numeric(df['Mark'], errors='coerce')

# --- Pivot to get one row per student ---
pivot = df.pivot_table(index=['Emplid', 'Name'], columns='Course', values='Mark', aggfunc='first').reset_index()

# --- Identify subject columns ---
subject_cols = [col for col in pivot.columns if col not in ['Emplid', 'Name']]

# --- TEMP GPA Calculation before normalization ---
pivot['GPA'] = (pivot[subject_cols].sum(axis=1) / (pivot[subject_cols].notna().sum(axis=1) * 25)).clip(upper=4.0)

# --- Now normalize the features only ---
for col in subject_cols:
    mu = pivot[col].dropna().mean()
    pivot[col] = pivot[col].fillna(mu)
    pivot[col] = (pivot[col] - mu) / mu

# --- Train/test split ---
X = pivot[subject_cols]
y = pivot['GPA']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# --- Train the model ---
model = HistGradientBoostingRegressor(random_state=42)
model.fit(X_train, y_train)

# --- Save the model using cloudpickle ---
os.makedirs("Machine Learning", exist_ok=True)
with open("Machine Learning/gpa_hist_model_cp.pkl", "wb") as f:
    cloudpickle.dump({
        'model': model,
        'subject_cols': subject_cols
    }, f)

print("✅ Model retrained and saved successfully!")
