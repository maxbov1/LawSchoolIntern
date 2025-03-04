# LawIntern Project

LawIntern is a web-based tool that allows users to upload CSV files, process data, and store it in a MySQL database. 
It is containerized using Docker for easy deployment.

## Folder Structure
📂 LawIntern/ │-- 📁 dataBase/ # Database connection and query functions
│-- 📁 dataUpload/ # CSV upload and processing logic
│-- 📁 templates/ # HTML templates for UI 
│-- 📄 main.py # App entry point (Flask server)
│-- 📄 Dockerfile # Docker container setup
│-- 📄 docker-compose.yml # Multi-container setup
│-- 📄 requirements.txt # Python dependencies
│-- 📄 .env # environment variables/secrets


## Setup 
|-- Go to setup.txt

## App flow
|-- 1. User uploads file through /uploads
|-- 2. Data is extracted through uploadCSV.py, which calls extractData.py
|-- 3. Data then encrypted within uploadCSV.py, using dataBase/encrypt functions
|-- 4. Data transfered to RDB using dataBase/dataFrameToTable.py 
|-- 5. Success message broadcasted so long data passes all checks and successfully saved to RDB.
