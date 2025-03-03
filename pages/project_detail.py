import dash
from dash import html
import pandas as pd
import urllib.parse  # Handles URL decoding
from data import load_data

df = load_data()

# Ensure 'Comments Due Date' is converted to datetime (if it hasn't been already)
df["Comments Due Date"] = pd.to_datetime(df["Comments Due Date"], errors="coerce")

def layout(project_name):
    # Decode URL to handle spaces and special characters
    decoded_name = urllib.parse.unquote(project_name).strip()

    # Match project name with DataFrame (case insensitive)
    filtered_df = df[df["Project Name"].str.strip().str.lower() == decoded_name.lower()]

    # Handle missing project
    if filtered_df.empty:
        return html.Div([
            html.H1("Project Not Found", className="project-detail-not-found"),
            html.A("⬅ Return to Home", href="/", className="project-detail-back-button")
        ], className="project-detail-page")

    # Extract project data
    project_data = filtered_df.iloc[0]

    # Ensure 'Comments Due Date' is a datetime before formatting
    comments_due = project_data["Comments Due Date"]
    if pd.notna(comments_due):  # Check if not NaN
        if isinstance(comments_due, str):  # Convert to datetime if still a string
            comments_due = pd.to_datetime(comments_due, errors="coerce")
        if pd.notna(comments_due):  # If conversion was successful
            status_text = f"📅 Comments Due: {comments_due.strftime('%m/%d/%Y')}"
        else:
            status_text = "⏳ Awaiting Resubmittal"
    else:
        status_text = "⏳ Awaiting Resubmittal"

    # Get submission number
    submission_number = f"📌 Submission #: {project_data['Submission Number']}" if pd.notna(project_data["Submission Number"]) else "N/A"

    # Process requirements
    submitted_list = str(project_data["Submitted Requirements"]).split(", ") if pd.notna(project_data["Submitted Requirements"]) else []
    all_items_list = str(project_data["Requirements"]).split(", ") if pd.notna(project_data["Requirements"]) else []
    submittal_requirements = html.Ul([html.Li(f"{'✅' if item in submitted_list else '❌'} {item}") for item in all_items_list])

    # Process TRC Reviewers
    reviewed_list = str(project_data["Reviewed TRC Departments"]).split(", ") if pd.notna(project_data["Reviewed TRC Departments"]) else []
    all_reviewers = str(project_data["TRC Reviewers"]).split(", ") if pd.notna(project_data["TRC Reviewers"]) else []
    trc_reviewers = html.Ul([html.Li(f"{'✅' if reviewer in reviewed_list else '❌'} {reviewer}") for reviewer in all_reviewers])

    return html.Div([
        html.Div([
            html.H1(decoded_name, className="project-detail-title"),
            html.H3(status_text, className="project-detail-status"),
            html.P(submission_number, className="project-detail-submission"),

            html.Div([
                html.Div([
                    html.H4("📌 Submittal Requirements", className="project-detail-box-title"),
                    submittal_requirements
                ], className="project-detail-box"),

                html.Div([
                    html.H4("📌 TRC Reviewers", className="project-detail-box-title"),
                    trc_reviewers
                ], className="project-detail-box"),
            ], className="project-detail-info-container"),

            html.A("⬅", href="/", className="project-detail-back-button"),
        ], className="project-detail-container"),
    ], className="project-detail-page")
