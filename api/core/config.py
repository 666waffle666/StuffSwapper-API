from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # DB
    DATABASE_URL: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str
    TOKEN_EXPIRE_MINUTES: int

    # REDIS
    REDIS_URL: str

    # Mailer
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_TLS: bool
    MAIL_SSL: bool

    VERIFICATION_TOKEN_EXPIRE_HOURS: int
    RESEND_LIMIT_PER_HOUR: int

    FRONTEND_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


Config = Settings()  # type: ignore
