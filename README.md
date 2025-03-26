# Cramerton Development Status Tracker

A web application for tracking development projects in Cramerton.

## Local Development

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your Azure credentials:
```
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER_NAME=your_container_name
```

4. Run the application locally:
```bash
uvicorn backend.main:app --reload
```

## Deployment

This application is configured for deployment on Azure App Service. Here's how to deploy:

1. Install the Azure CLI and log in:
```bash
az login
```

2. Create an Azure App Service:
```bash
az group create --name cramerton-tracker-rg --location eastus
az appservice plan create --name cramerton-tracker-plan --resource-group cramerton-tracker-rg --sku B1 --is-linux
az webapp create --resource-group cramerton-tracker-rg --plan cramerton-tracker-plan --name cramerton-tracker --runtime "PYTHON:3.11"
```

3. Configure environment variables in Azure Portal:
   - Go to your App Service
   - Navigate to Configuration > Application settings
   - Add the following settings:
     - AZURE_STORAGE_CONNECTION_STRING
     - AZURE_STORAGE_CONTAINER_NAME

4. Deploy using Azure CLI:
```bash
az webapp up --name cramerton-tracker --resource-group cramerton-tracker-rg --runtime "PYTHON:3.11"
```

## Project Structure

- `backend/`: FastAPI backend application
- `frontend/`: Dash frontend application
- `pages/`: Dash page components
- `assets/`: Static assets (CSS, images, etc.)

## Features

- Track development projects by category
- View project details and status
- Update project information
- Manage comments and due dates
- Azure Blob Storage integration for data persistence

## Tech Stack

- Frontend: React.js with TypeScript
- Backend: FastAPI (Python)
- Database: PostgreSQL
- Authentication: JWT

## Setup Instructions

1. Clone the repository
2. Install dependencies:
   ```bash
   # Frontend
   cd frontend
   npm install

   # Backend
   cd backend
   pip install -r requirements.txt
   ```
3. Set up environment variables
4. Run the application:
   ```bash
   # Frontend
   cd frontend
   npm start

   # Backend
   cd backend
   uvicorn main:app --reload
   ```

## Project Structure

```
├── frontend/           # React frontend application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API services
│   │   └── styles/       # CSS styles
│   └── public/           # Static assets
│
└── backend/           # FastAPI backend application
    ├── app/
    │   ├── api/          # API routes
    │   ├── models/       # Database models
    │   └── services/     # Business logic
    └── tests/            # Test files
``` 