from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str = "placeholder"
    ANTHROPIC_API_KEY: str = "placeholder"
    TRM_LABS_API_KEY: str = "placeholder"
    
    # Skyflow
    SKYFLOW_VAULT_ID: str = "placeholder"
    SKYFLOW_VAULT_URL: str = "placeholder"
    SKYFLOW_BEARER_TOKEN: str = "placeholder"
    SKYFLOW_FUNCTION_ID: str = "placeholder"  # Optional: for vault-confined AI processing
    SKYFLOW_CONNECTION_URL: str = "placeholder"  # Connection URL for invoking functions
    SKYFLOW_ACCOUNT_ID: str = "placeholder"  # Account ID for Skyflow API calls
    SKYFLOW_USE_MCP_SERVER: bool = False  # Set to True to use MCP server for PII detection (requires working MCP server)
    
    # Sanity
    SANITY_PROJECT_ID: str = "placeholder"
    SANITY_DATASET: str = "production"
    SANITY_API_TOKEN: str = "placeholder"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        # Look for .env in project root (one level up from backend/)
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")

settings = Settings()
