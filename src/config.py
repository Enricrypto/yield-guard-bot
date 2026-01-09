"""
Configuration module for the DeFi Yield Guard Bot.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    def __init__(self):
        # Database configuration
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///data/simulations.db")

        # Extract database path for sqlite
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            self.database_path = str(Path(db_path).resolve())
        else:
            # For PostgreSQL or other databases, use the full URL
            self.database_path = self.database_url

        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        # API Keys
        self.aave_api_key = os.getenv("AAVE_API_KEY", "")
        self.compound_api_key = os.getenv("COMPOUND_API_KEY", "")

        # RPC URLs
        self.ethereum_rpc_url = os.getenv(
            "ETHEREUM_RPC_URL", "https://mainnet.infura.io/v3/your_infura_key"
        )
        self.polygon_rpc_url = os.getenv(
            "POLYGON_RPC_URL", "https://polygon-rpc.com"
        )

        # Bot settings
        self.check_interval_seconds = int(os.getenv("CHECK_INTERVAL_SECONDS", "300"))
        self.alert_threshold_percentage = float(
            os.getenv("ALERT_THRESHOLD_PERCENTAGE", "5.0")
        )

        # Notification settings
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.email_address = os.getenv("EMAIL_ADDRESS", "")
        self.email_password = os.getenv("EMAIL_PASSWORD", "")

        # Environment
        self.environment = os.getenv("ENVIRONMENT", "development")

    def __repr__(self):
        return f"Config(database_url={self.database_url}, environment={self.environment})"
