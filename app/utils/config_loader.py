from pydantic import BaseModel, Field, ValidationError
from typing import Dict, List
import json
import logging
from flask import g


class DataSourceConfig(BaseModel):
    source_name: str
    fields: Dict[str, str]  # Field name and expected type

class ConfigData(BaseModel):
    target_variable: str
    identifier: str
    sensitive_columns: List[str]
    data_sources: Dict[str, Dict[str, str]]

def load_config() -> ConfigData:
    try:
        config_path = f'config/project_{g.project_id}/data_source_config.json'
        with open(config_path, 'r') as file:
            config_data = json.load(file)
        config = ConfigData(**config_data)
        logging.info("Configuration loaded successfully!")
        return config
    except ValidationError as e:
        logging.error(f"Configuration validation error: {e}")
        raise ValueError(f"Configuration validation error: {e}")
    except FileNotFoundError:
        logging.error(f"Configuration file not found at {CONFIG_PATH}")
        raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON format in configuration file: {CONFIG_PATH}")
        raise ValueError(f"Invalid JSON format in configuration file: {CONFIG_PATH}")
    except Exception as e:
        logging.error(f"Unexpected error loading configuration: {e}")
        raise ValueError(f"Unexpected error loading configuration: {e}")

