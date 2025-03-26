from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import csv
import os
from azure.storage.blob import BlobServiceClient
import io
import logging
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
API_KEY = os.getenv("API_KEY")

# Set up logging for debugging and monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cramerton Development Tracker API")

# Configure rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure configuration
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
blob_name = "Development_Status.csv"

if not connection_string or not container_name:
    logger.error("Missing Azure Storage credentials")
    raise ValueError("Missing Azure Storage credentials")

# Security utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
api_key_header = APIKeyHeader(name="X-API-Key")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data.username

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

def get_blob_client():
    """Get Azure Blob client for file operations"""
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        return container_client.get_blob_client(blob_name)
    except Exception as e:
        logger.error(f"Failed to connect to Azure Storage: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to connect to Azure Storage: {str(e)}")

def load_data() -> List[Dict[str, Any]]:
    """Load and parse CSV data from Azure Storage"""
    try:
        blob_client = get_blob_client()
        csv_data = blob_client.download_blob().readall().decode('utf-8')
        
        # Parse CSV data
        reader = csv.DictReader(io.StringIO(csv_data))
        projects = list(reader)
        
        # Clean up empty values
        for project in projects:
            for key, value in project.items():
                if not value:
                    project[key] = None
        
        logger.info(f"Loaded {len(projects)} projects")
        return projects
    except Exception as e:
        logger.error(f"Failed to load data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")

def save_data(projects: List[Dict[str, Any]]):
    """Save project data back to Azure Storage"""
    if not projects:
        return
        
    try:
        # Write to CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=projects[0].keys())
        writer.writeheader()
        writer.writerows(projects)
        
        # Upload to Azure
        blob_client = get_blob_client()
        blob_client.upload_blob(output.getvalue().encode('utf-8'), overwrite=True)
    except Exception as e:
        logger.error(f"Failed to save data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save data: {str(e)}")

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint to get access token"""
    # In production, verify against a database
    if form_data.username != os.getenv("ADMIN_USERNAME") or form_data.password != os.getenv("ADMIN_PASSWORD"):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
async def read_root():
    """API health check endpoint"""
    return {"message": "Welcome to Cramerton Development Tracker API"}

@app.get("/projects")
@limiter.limit("5/minute")
async def get_projects(request: Request, current_user: str = Depends(get_current_user)):
    """Get all projects"""
    try:
        projects = load_data()
        return projects
    except Exception as e:
        logger.error(f"Failed to get projects: {str(e)}")
        raise

@app.get("/projects/{category}")
@limiter.limit("5/minute")
async def get_projects_by_category(category: str, request: Request, current_user: str = Depends(get_current_user)):
    """Get projects filtered by category"""
    projects = load_data()
    return [p for p in projects if p['Category'] == category]

@app.get("/projects/{category}/{project_name}")
@limiter.limit("5/minute")
async def get_project_details(category: str, project_name: str, request: Request, current_user: str = Depends(get_current_user)):
    """Get details for a specific project"""
    projects = load_data()
    project = next((p for p in projects if p['Category'] == category and p['Project Name'] == project_name), None)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.put("/projects/{category}/{project_name}")
@limiter.limit("3/minute")
async def update_project(category: str, project_name: str, project_data: dict, request: Request, current_user: str = Depends(get_current_user)):
    """Update an existing project"""
    try:
        projects = load_data()
        project_index = next((i for i, p in enumerate(projects) 
                            if p['Category'] == category and p['Project Name'] == project_name), -1)
        
        if project_index == -1:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update only existing fields
        for key, value in project_data.items():
            if key in projects[project_index]:
                projects[project_index][key] = value
        
        save_data(projects)
        return {"message": "Project updated successfully"}
    except Exception as e:
        logger.error(f"Failed to update project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")

@app.post("/projects")
@limiter.limit("3/minute")
async def add_project(project_data: dict, request: Request, current_user: str = Depends(get_current_user)):
    """Add a new project"""
    try:
        projects = load_data()
        projects.append(project_data)
        save_data(projects)
        return {"message": "Project added successfully"}
    except Exception as e:
        logger.error(f"Failed to add project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add project: {str(e)}")

@app.delete("/projects/{category}/{project_name}")
@limiter.limit("3/minute")
async def delete_project(category: str, project_name: str, request: Request, current_user: str = Depends(get_current_user)):
    """Delete a project"""
    try:
        projects = load_data()
        original_count = len(projects)
        
        # Remove the project
        projects = [p for p in projects if not (p['Category'] == category and p['Project Name'] == project_name)]
        
        if len(projects) == original_count:
            raise HTTPException(status_code=404, detail="Project not found")
        
        save_data(projects)
        return {"message": "Project deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 