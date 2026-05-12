from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    sd_ivitrina_bot_token: str
    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"
    vitrina_api_base: str = "https://vitrina-api.jurta.kz"

    vitrina_ai_bot_token: str
    dify_api_base: str = "https://api.dify.ai/v1"
    dify_bearer_token: str

    log_level: str = "INFO"
    log_dir: str = "/app/logs"


settings = Settings()
