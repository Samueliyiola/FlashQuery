import os
from dataclasses import dataclass
from dotenv import load_dotenv #To load environment variables from a .env file

# Load environment variables from a .env file into the process environment
load_dotenv()


@dataclass
class Config:
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", 5432))
    db_name: str = os.getenv("DB_NAME", "testdb")
    db_user: str = os.getenv("DB_USER", "user")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_sslmode: str = os.getenv("DB_SSLMODE", "disable")



    # DOCKER SANDBOX(FOR TESTING FIXES BEFORE RECOMMENDING TO USE IN PRODUCTION)
    sandbox_image: str = os.getenv("SANDBOX_IMAGE", "flashquery-postgres-sandbox:latest")
    sandbox_port: int = int(os.getenv("SANDBOX_PORT", 5433))


    # FOR LLM USED IN PHASE 3
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", 500))



    # FOR GITHUB USED IN PHASE 4
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_repo: str = os.getenv("GITHUB_REPO", "")



    # LOGGING CONFIGURATION
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_dir: str = os.getenv("LOG_DIR", "logs")


    # BENCHMARK
    benchmark_trials: int = int(os.getenv("BENCHMARK_TRIALS", "5"))
    benchmark_warmup: int = int(os.getenv("BENCHMARK_WARMUP", "2"))



    # FUNCTION TO VALIDATE IF ALL CONFIG VALUES ARE PRESENT AND NOT EMPTY
    def validate(self) -> None:
        errors = []

        if not self.db_password:
            errors.append("DB_PASSWORD is not set. Please set it in the environment variables or .env file.")
        
        if self.llm_api_key and not self.llm_model:
            errors.append("LLM_MODEL is required if LLM_API_KEY is set.")
        if self.github_token and not self.github_repo:
            errors.append("GITHUB_REPO is required if GITHUB_TOKEN is set.")
        if errors:
            raise ValueError("Configuration errors found:\n" + "\n".join(errors))



config = Config()


