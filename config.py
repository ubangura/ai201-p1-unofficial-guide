from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- LLM ---
    GROQ_API_KEY: SecretStr
    LLM_MODEL: str = "llama-3.3-70b-versatile"

    # --- Embeddings ---
    EMBEDDING_MODEL: str = "multi-qa-MiniLM-L6-cos-v1"

    # --- Vector store ---
    CHROMA_COLLECTION: str = "umd_cs_professors"
    CHROMA_PATH: Path = Path("./chroma_db")

    # --- Retrieval ---
    N_RESULTS: int = 4

    # --- Documents ---
    DOCS_PATH: Path = Path("./docs")


settings = Settings()
