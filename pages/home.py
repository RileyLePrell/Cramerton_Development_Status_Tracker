import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import urllib.parse  # Handles URL encoding
from data import load_data

df = load_data()  # Load CSV data

# Convert 'Comments Due Date' to datetime format, handling NaN values
df["Comments Due Date"] = pd.to_datetime(df["Comments Due Date"], errors="coerce")

# Function to sort projects
def sort_projects(df):
    return df.sort_values(
        by=["Comments Due Date", "Project Name"], 
        ascending=[True, True], 
        na_position="last"  # NaN dates will go to the bottom
    )

# Define categories
categories = ["Rezoning", "Preliminary Plat", "Construction Drawings", "Final Plat"]

# Generate category boxes
category_cards = []
for category in categories:
    projects = sort_projects(df[df["Category"] == category])  # Apply sorting

    # Create project buttons within category (Encode project name for URL safety)
    project_buttons = [
        dbc.Button(
            f"{row['Project Name']}\n{'Comments Due: ' + row['Comments Due Date'].strftime('%m/%d/%Y') if pd.notna(row['Comments Due Date']) else '⏳ Awaiting Resubmittal'}",
            href=f"/project/{urllib.parse.quote(row['Project Name'])}",  # Ensure URL is safe
            className="home-project-button",
        ) for _, row in projects.iterrows()
    ]

    category_cards.append(
        dbc.Col([
            html.Div([
                html.H4(category, className="home-category-title"),
                html.Div(project_buttons, className="home-project-container")  # Scrollable project list
            ], className="home-category-box"),
        ], width=3)
    )

# Home Page Layout
layout = html.Div([
    html.Div([
        html.H1("Welcome", className="welcome-text"),
        html.H2("Cramerton Plan Review Tracker", className="tracker-text")
    ], className="home-header-container"),

    dbc.Row(category_cards, className="category-row", justify="center")  # Ensure center alignment
], className="home-page")  # 🔥 Ensure this page has the .home-page class

