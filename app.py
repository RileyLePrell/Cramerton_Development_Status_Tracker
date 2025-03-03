import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import pages.project_detail as project_detail
import pages.home as home

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Define available stylesheets for different pages
home_stylesheet = "assets/home.css"
project_stylesheet = "assets/project.css"

# App Layout
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),  # Tracks current page URL
    html.Link(id="stylesheet", rel="stylesheet", href=home_stylesheet),  # Dynamic stylesheet
    html.Div(id="page-content")  # Placeholder for the content of the current page
])

# Callback to switch between Home Page and Project Detail Page
@app.callback(
    [Output("page-content", "children"), Output("stylesheet", "href")],
    [Input("url", "pathname")]
)
def display_page(pathname):
    if pathname and pathname.startswith("/project/"):
        return project_detail.layout(pathname.split("/")[-1]), project_stylesheet  # Load project page + styles
    return home.layout, home_stylesheet  # Load home page + styles

# Run server
if __name__ == '__main__':
    app.run_server(debug=True)
