# LawIntern Project
    
LawIntern is a web-based data management platform that allows users to upload CSV files, validate data with Pydantic models, and store it securely in a MySQL database. It supports real-time schema visualization and data encryption for sensitive fields.

## Folder Structure
```
📂 LawIntern/
├── app/                   # Main application logic
│   ├── dataBase/           # Database functions and encryption
│   │   ├── dataFrameToTable.py   # Handles data insertion
│   │   ├── dbBuilder.py         # Builds database structure
│   │   ├── encrypt.py           # Data encryption utilities
│   │   └── schema.txt           # Database schema file
│   ├── dataUpload/        # CSV file upload and processing
│   │   ├── extractData.py       # Extracts data from CSV
│   │   ├── tools/               # Utility functions
│   │   └── uploadCsv.py         # Handles CSV uploads
│   ├── utils/             # Utility scripts and dynamic model generation
│   │   ├── config_loader.py     # Loads configuration files
│   │   └── dynamic_models.py    # Generates models dynamically
│   └── main.py                 # Flask application entry point
├── config/                # Configuration storage
│   └── data_source_config.json  # Data source configuration file
├── templates/             # HTML templates for the UI
│   ├── base.html               # Base template
│   ├── config.html             # Configuration page
│   ├── home.html               # Home page
│   └── upload.html             # File upload page
├── static/                # Static assets (CSS, JS)
│   ├── script.js               # Frontend scripting
│   └── style.css               # Frontend styling
├── requirements.txt        # Python dependencies
├── setup.md                # Setup instructions
├── README.md               # Project documentation
├── Dockerfile              # Docker setup
├── docker-compose.yml      # Multi-container setup
├── uploads/                # Directory for uploaded files
└── venv/                   # Python virtual environment
```

## Setup 
|-- Go to setup.txt

## App flow

Configuration:

    User sets up data configuration through the /config form. The configuration is stored in data_source_config.json for modular processing and validation.

File Upload:

    User uploads a CSV file via the /uploads endpoint. The uploaded file is saved to the uploads/ directory.

Data Extraction and Processing:

    The file is processed using uploadCsv.py, which calls extractData.py for data extraction.Data is transformed and prepared using utility functions from dataUpload/tools.

Data Validation:

    Extracted data is validated against the user-defined configuration using Pydantic models from utils/dynamic_models.py. This ensures consistency and accuracy before insertion.

Data Encryption:

    Sensitive fields are encrypted using the functions from dataBase/encrypt.py.

Database Insertion:

    Validated and encrypted data is inserted into the relational database using dataFrameToTable.py. The database structure is maintained and managed via dbBuilder.py.

Success Message:
    A success message is displayed upon successful validation and database insertion.
