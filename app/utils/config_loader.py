from pydantic import BaseModel, ValidationError
from typing import Dict, List
import json
import logging
from flask import g
from utils.path_helper import get_data_source_config_path

class DataSourceConfig(BaseModel):
    source_name: str
    fields: Dict[str, str]  # Field name and expected type

class ConfigData(BaseModel):
    target_variable: str
    identifier: str
    sensitive_columns: List[str]
    data_sources: Dict[str, Dict[str, str]]

def load_config() -> ConfigData:
    config_path = get_data_source_config_path(g.project_id)

    try:
        with config_path.open('r') as file:
            config_data = json.load(file)
        config = ConfigData(**config_data)
        logging.info(f"✅ Configuration loaded successfully from {config_path}")
        return config

    except ValidationError as e:
        logging.error(f"❌ Configuration validation error: {e}")
        raise ValueError(f"Configuration validation error: {e}")

    except FileNotFoundError:
        logging.error(f"❌ Configuration file not found at {config_path}")
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    except json.JSONDecodeError:
        logging.error(f"❌ Invalid JSON format in configuration file: {config_path}")
        raise ValueError(f"Invalid JSON format in configuration file: {config_path}")

    except Exception as e:
        logging.error(f"❌ Unexpected error loading configuration: {e}")
        raise ValueError(f"Unexpected error loading configuration: {e}")

