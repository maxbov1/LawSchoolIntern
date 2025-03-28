from pydantic import BaseModel, create_model, ValidationError
from .config_loader import load_config
import logging
from typing import Optional

def create_dynamic_model(data_source_name: str):
    try:
        config = load_config()
        fields = config.data_sources.get(data_source_name)

        if fields is None:
            raise ValueError(f"Data source '{data_source_name}' not found in configuration.")

        # Map configuration data types to Pydantic optional types
        type_mapping = {
            'string': (Optional[str], None),
            'float': (Optional[float], None),
            'int': (Optional[int], None),
            'bool': (Optional[bool], None)
        }

        model_fields = {
            field_name: type_mapping.get(field_type, (Optional[str], None))  # Default to optional string
            for field_name, field_type in fields.items()
        }

        # Dynamically create a Pydantic model
        model = create_model(data_source_name.capitalize(), **model_fields)
        logging.info(f"Dynamically created model for data source: {data_source_name}")
        return model
    except ValueError as e:
        logging.error(f"Error creating dynamic model for '{data_source_name}': {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in creating model for '{data_source_name}': {e}")
        raise

