#########################################################################
# Title  : Program Overview - Subject & Plan Mapping Module
# Author : Kevin Ryan Noronha
# Editor : Disha Khurana 
# Updated: 1 June 2025 
# Updates: Cleaned subject and plan data, created overview of student pathways, 
#          added clickable course links, beautified table display, 
#          incorporated comments for clarity, and added conditional back button.
#########################################################################

# Importing necessary libraries 
import os
import pandas as pd
from flask import Blueprint, render_template, current_app, url_for, flash

# Creating Flask blueprint for the pathway section
pathway_bp = Blueprint('pathway', __name__, template_folder='templates')

@pathway_bp.route('/')
def home():
    # Define the path to the Excel data file in the 'data' folder
    data_folder = os.path.join(current_app.root_path, 'data')
    file_path = os.path.join(data_folder, 'CourseDetails.xlsx')

    # Checking if the file exists
    if not os.path.exists(file_path):
        flash("CourseDetails.xlsx not found in the data/ folder.", 'error')
        return render_template('pathway_overview.html', table_html=None, title='Pathway Overview')

    # Loading the Excel sheet named 'PathwayOverview'
    xls = pd.ExcelFile(file_path)
    df = pd.read_excel(xls, 'PathwayOverview').fillna('')

    # Keeping original course code and course name for hyperlinking
    df['code_raw'] = df['Course_Code'].astype(str)
    df['name_raw'] = df['Final_Course'].astype(str)

    # Making course code a clickable link
    df['Course_Code'] = df['code_raw'].apply(
        lambda code: f'<a href="{url_for("pathway.course_details", code=code)}">{code}</a>'
    )

    # Making final course name a clickable link (if available)
    def build_name_link(row):
        code = row["code_raw"]
        name = row["name_raw"]
        if name.strip():
            return f'<a href="{url_for("pathway.course_details", code=code)}">{name}</a>'
        return ''
    
    df['Final_Course'] = df.apply(build_name_link, axis=1)

    # Selecting and renaming only the relevant columns for display
    display_df = df[['Course_Code', 'Final_Course']]
    display_df.columns = display_df.columns.str.replace('_', ' ')

    # Converting DataFrame to HTML table
    table_html = display_df.to_html(index=False, classes='table table-bordered data-table', escape=False)
    return render_template('pathway_overview.html', table_html=table_html, title='Pathway Overview')

@pathway_bp.route('/course/<code>')
def course_details(code):
    # Loading course data
    data_folder = os.path.join(current_app.root_path, 'data')
    file_path = os.path.join(data_folder, 'CourseDetails.xlsx')
    xls = pd.ExcelFile(file_path)

    courses = pd.read_excel(xls, 'Courses').fillna('')
    df = courses[courses['Parent_Program_Code'].astype(str) == code]

    # Error message if no data found for the course code
    if df.empty:
        flash(f"No pathway details for {code}.", 'error')
        return render_template('pathway_overview.html', table_html=None, title=f'Courses under {code}', show_back_button=True)

    # Making course code and course name clickable to show subject details
    df['Program_Code'] = df['Program_Code'].apply(
        lambda c: f'<a href="{url_for("pathway.subject_details", code=c)}">{c}</a>'
    )
    df['Course_Name'] = df['Course_Name'].apply(
        lambda c: f'<a href="{url_for("pathway.subject_details", code=code)}">{c}</a>'
    )

    # Selecting and renaming relevant columns
    display_df = df[['Program_Code', 'Course_Name', 'Years', 'Credits_Transferred']]
    display_df.columns = display_df.columns.str.replace('_', ' ')

    table_html = display_df.to_html(index=False, classes='table table-bordered data-table', escape=False)
    return render_template('pathway_overview.html', table_html=table_html, title=f'Courses under {code}', show_back_button=True)

@pathway_bp.route('/course/<code>/subjects')
def subject_details(code):
    # Loading subject mapping data
    data_folder = os.path.join(current_app.root_path, 'data')
    file_path = os.path.join(data_folder, 'CourseDetails.xlsx')
    xls = pd.ExcelFile(file_path)

    cs = pd.read_excel(xls, 'CourseSubjects').fillna('')
    sub = pd.read_excel(xls, 'Subjects').fillna('')
    df = cs[cs['Program_Code'].astype(str) == code]

    # Error message if no subjects are mapped to the program
    if df.empty:
        flash(f"No subjects found for {code}.", 'error')
        return render_template('pathway_overview.html', table_html=None, title=f'Subjects for {code}', show_back_button=True)

    # Merging subject details with mapping
    df = df.merge(
        sub[['Subject_Code', 'Subject_Title', 'CreditPoints', 'Hours', 'Campus']],
        on='Subject_Code', how='left'
    )

    # Renaming column for display
    df.rename(columns={'Subject_Title': 'Subject_Name'}, inplace=True)

    # Selecting and renaming final columns to be shown
    display_df = df[['Subject_Code', 'Subject_Name', 'CreditPoints', 'Hours', 'Core_YN', 'Elective_YN', 'Campus']]
    display_df.rename(columns={
        'Subject_Code': 'Subject Code',
        'Subject_Name': 'Subject Name',
        'CreditPoints': 'Credit Points',
        'Hours': 'Hours',
        'Core_YN': 'Core (Y/N)',
        'Elective_YN': 'Elective (Y/N)',
        'Campus': 'Campus'
    }, inplace=True)

    table_html = display_df.to_html(index=False, classes='table table-bordered data-table', escape=False)
    return render_template('pathway_overview.html', table_html=table_html, title=f'Subjects for {code}', show_back_button=True)
