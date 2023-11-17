import json
import sqlite3
from datetime import datetime, timedelta
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
import socket
import fcntl
import struct

app = FastAPI(title="x-ui Mirza", version="0.0.1")
admin = APIRouter()
users = APIRouter()
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
URLPANEL = "/etc/x-ui/x-ui.db"


class getdatauser(BaseModel):
    username: str | None = None
    status: bool | None = None
    uuid: str | None = None
    data_limit: int | None = None
    total: int | None = None
    expire: int | None = None
    port: int | None = None
    protocol: str | None = None
    network: str | None = None
    message: str | None = None


class User(BaseModel):
    username: str


class TokenData(BaseModel):
    username: str | None = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="admin/token")

def get_ip_address(ifname):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ip_address = socket.inet_ntoa(fcntl.ioctl(
            sock.fileno(),
            0x8915, 
            struct.pack('256s', ifname[:15].encode('utf-8'))
        )[20:24])
        return ip_address
    finally:
        sock.close()


def get_user(db, username: str):
    for users in db:
        if username in users:
            user_dict = users
            return user_dict


def authenticate_user(date, username: str, password: str):
    user = get_user(date, username)
    if not user:
        return False
    if user[1] != password:
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    global URLPANEL
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    with sqlite3.connect(URLPANEL) as connect:
        cu = connect.cursor()
        cu.execute("SELECT username,password FROM users")
        user = get_user(cu.fetchall(), username=token_data.username)
        if user is None:
            raise credentials_exception
    return user


@admin.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    global URLPANEL
    with sqlite3.connect(URLPANEL) as connect:
        cu = connect.cursor()
        cu.execute("SELECT username,password FROM users")
        user = authenticate_user(cu.fetchall(), form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}


@users.get(
    "/getusers/{username}",
    response_model=getdatauser,
    response_model_exclude_unset=True,
)
def Get_Date_User(username, current_user: User = Depends(get_current_user)):
    global URLPANEL
    """show data user"""
    with sqlite3.connect(URLPANEL) as connect:
        cu = connect.cursor()
        cu.execute(f"SELECT * FROM inbounds WHERE remark = '{username}'")
        users_data = cu.fetchall()
        if not users_data:
            return {"message": "User Not Found"}
        settinuser = json.loads(users_data[0][11])["clients"][0]["id"]
        settingnetwork = json.loads(users_data[0][12])
        return {
            "username": username,
            "status": users_data[0][6],
            "uuid": settinuser,
            "data_limit": int(users_data[0][2]) + int(users_data[0][3]),
            "total": users_data[0][4],
            "expire": users_data[0][7],
            "port": users_data[0][9],
            "protocol": users_data[0][10],
            "network": settingnetwork["network"],
        }


app.include_router(admin, prefix="/admin", tags=["Admin"])
app.include_router(users, prefix="/users", tags=["Users"])
ip = get_ip_address("eth0")
if __name__ == "__main__":
    uvicorn.run("main:app", host=ip, port=8000, log_level="info")
