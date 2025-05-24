from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

def get_project_config_dir(project_id: str) -> Path:
    return BASE_DIR / "app" / "config" / f"project_{project_id}"

def get_data_source_config_path(project_id: str) -> Path:
    return get_project_config_dir(project_id) / "data_source_config.json"

def get_model_config_path(project_id: str, model_name: str) -> Path:
    return get_model_config_dir(project_id) / model_name

def get_model_config_dir(project_id: str) -> Path:
    return get_project_config_dir(project_id) / "model_configs"

def get_temp_upload_path(project_id: str, filename: str) -> Path:
    return BASE_DIR / "temp" / f"project_{project_id}" / filename

def get_project_upload_path(project_id: str, filename: str) -> Path:
    return BASE_DIR / "uploads" / f"project_{project_id}" / filename
