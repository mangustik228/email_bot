# config.py
from typing import Literal

from dotenv import load_dotenv
from pydantic import EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Google(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GOOGLE_")
    port: int
    email: EmailStr
    server: str
    password: str

class Bot(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BOT_")
    token:str
    client_id:int # id пользователя куда высылать уведомления

class TgClient(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TG_CLIENT_")
    api_id: str
    api_hash: str
    bot_name: str
    session_name: str

class Gemini(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GEMINI_")
    api_key:str


class Settings(BaseSettings):
    google: Google = Google()        # type: ignore
    gemini: Gemini = Gemini()        # type: ignore
    tg_client: TgClient = TgClient() # type: ignore
    bot: Bot = Bot()                 # type: ignore
    MODE: Literal["DEV","PROD"]

settings = Settings() # type: ignore