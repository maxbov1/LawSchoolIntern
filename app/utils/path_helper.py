from pathlib import Path
import logging

BASE_DIR = Path(__file__).resolve().parents[2]
logging.info(f"📂 [INIT] BASE_DIR = {BASE_DIR}")

def get_project_config_dir(project_id: str) -> Path:
    path = BASE_DIR / "app" / "config" / f"project_{project_id}"
    logging.info(f"📁 get_project_config_dir({project_id}) = {path}")
    return path

def get_data_source_config_path(project_id: str) -> Path:
    path = get_project_config_dir(project_id) / "data_source_config.json"
    logging.info(f"📁 get_data_source_config_path({project_id}) = {path}")
    return path

def get_model_config_path(project_id: str, model_name: str) -> Path:
    if not model_name.endswith(".json"):
        model_name += ".json"
    path = BASE_DIR / "app" / "config" / f"project_{project_id}" / "model_configs" / model_name
    logging.info(f"📁 get_model_config_path({project_id}, {model_name}) = {path}")
    return path

def get_model_config_dir(project_id: str) -> Path:
    path = get_project_config_dir(project_id) / "model_configs"
    logging.info(f"📁 get_model_config_dir({project_id}) = {path}")
    return path

def get_temp_upload_path(project_id: str, filename: str) -> Path:
    path = BASE_DIR / "temp" / f"project_{project_id}" / filename
    logging.info(f"📁 get_temp_upload_path({project_id}, {filename}) = {path}")
    return path

def get_project_upload_path(project_id: str, filename: str) -> Path:
    path = BASE_DIR / "uploads" / f"project_{project_id}" / filename
    logging.info(f"📁 get_project_upload_path({project_id}, {filename}) = {path}")
    return path

