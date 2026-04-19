import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
import os
import dotenv

dotenv.load_dotenv()

with open(os.getenv("PRIVATE_KEY_PATH"), "r") as private_file:
    PRIVATE_KEY = private_file.read()

with open(os.getenv("PUBLIC_KEY_PATH"), "r") as public_file:
    PUBLIC_KEY = public_file.read()

def hash_password(password:str) -> str:
    hash = bcrypt.hashpw(password.encode("utf-8"), salt=bcrypt.gensalt())
    return hash.decode("utf-8")

def verify_password(plain_password:str, hashed_password:str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, PRIVATE_KEY, algorithm=os.getenv("ALGORITHM"))
    return encode_jwt

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, PUBLIC_KEY, algorithms=[os.getenv("ALGORITHM")])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")