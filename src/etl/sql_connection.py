from pathlib import Path

import yaml
from sqlalchemy import create_engine


def load_db_config() -> dict:
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "db_config.local.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Saknar config-fil: {config_path}\n"
            f"Skapa filen genom att kopiera db_config.example.yaml till db_config.local.yaml."
        )

    #Här läser den in filen
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("Config-filen måste innehålla en YAML-dictionary.")

    required_keys = ["user", "password", "host", "port", "database"]
    missing = [key for key in required_keys if not config.get(key)]

    if missing:
        raise ValueError(f"Följande nycklar saknas i db_config.local.yaml: {missing}")

    return config


def sql_engine():
    config = load_db_config()

    engine = create_engine(
        f"postgresql+psycopg2://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}",
        connect_args={"connect_timeout": 5},
    )

    return engine