import os
from dotenv import load_dotenv

# Load variables from .env file before anything else reads them
load_dotenv()

class Config:

    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")
    LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-5.6-luna")

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    # TigerGraph Savanna
    TG_HOST = os.environ.get("TG_HOST")
    TG_GRAPH_NAME = os.environ.get("TG_GRAPH_NAME", "AGRI_EVIDENCE")
    
    TG_SECRET = os.environ.get("TG_SECRET")
    TG_API_TOKEN = os.environ.get("TG_API_TOKEN")
    
    TG_USERNAME = os.environ.get("TG_USERNAME")
    TG_PASSWORD = os.environ.get("TG_PASSWORD")

    APP_ENV = os.environ.get("APP_ENV", "development")

    @classmethod
    def validate(cls):
        missing = []

        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")

        if not cls.TG_HOST:
            missing.append("TG_HOST")

        if not cls.TG_SECRET and not cls.TG_API_TOKEN:
            missing.append("either TG_SECRET or TG_API_TOKEN")

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

if __name__ == "__main__":
    Config.validate()
