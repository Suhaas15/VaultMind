from pydantic_settings import BaseSettings
import os
class Settings(BaseSettings):
    OPENAI_API_KEY: str = "placeholder"
    ANTHROPIC_API_KEY: str = "placeholder"
    TRM_LABS_API_KEY: str = "placeholder"
    SKYFLOW_VAULT_ID: str = "placeholder"
    SKYFLOW_VAULT_URL: str = "placeholder"
    SKYFLOW_BEARER_TOKEN: str = "placeholder"
    SKYFLOW_FUNCTION_ID: str = "placeholder"  
    SKYFLOW_CONNECTION_URL: str = "placeholder"  
    SKYFLOW_ACCOUNT_ID: str = "placeholder"  
    SKYFLOW_USE_MCP_SERVER: bool = False  
    SANITY_PROJECT_ID: str = "placeholder"
    SANITY_DATASET: str = "production"
    SANITY_API_TOKEN: str = "placeholder"
    REDIS_URL: str = "redis://localhost:6379/0"
    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
settings = Settings()