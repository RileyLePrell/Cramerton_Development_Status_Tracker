from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def upload_csv():
    try:
        # Get Azure credentials from environment variables
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
        
        if not connection_string or not container_name:
            raise ValueError("Missing Azure Storage credentials in .env file")
        
        # Create the BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Get a reference to the container
        container_client = blob_service_client.get_container_client(container_name)
        
        # Create the container if it doesn't exist
        if not container_client.exists():
            container_client.create_container()
            print(f"Created container: {container_name}")
        
        # Get a reference to the blob
        blob_name = "Development_Status.csv"
        blob_client = container_client.get_blob_client(blob_name)
        
        # Upload the CSV file
        with open("Development_Status.csv", "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        
        print(f"Successfully uploaded {blob_name} to Azure Blob Storage")
        
    except Exception as e:
        print(f"Error uploading file: {str(e)}")

if __name__ == "__main__":
    upload_csv() 