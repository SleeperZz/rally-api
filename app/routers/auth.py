from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from ..databases import accounts_collection, User
from ..config import get_settings
from ..utils import get_password_hash, create_access_token, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={
        404: {
            'message': 'Not Found'
        }
    }
)

settings = get_settings()


def authenticate_user(username: str, password: str):
    user = accounts_collection.get_account_by_username(username)
    if not user:
        return False
    if not verify_password(password, user.get_password()):
        return False
    return user

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: dict):
    '''
    # Register a new user

    ### request body (form-encoded)
    - email: `str`
    - username: `str`
    - password: `str`

    ### response headers
    authorization: `str` (JWT)

    '''

    # Validate body
    if not body:
        raise HTTPException(status_code=400, detail="Body is required")
    if not body["email"]:
        raise HTTPException(status_code=400, detail="Email is required")
    if not body["username"]:
        raise HTTPException(status_code=400, detail="Username is required")
    if not body["password"]:
        raise HTTPException(status_code=400, detail="Password is required")

    # create new user
    new_user = User(
        email=body["email"],
        username=body["username"],
        password=get_password_hash(body["password"])
    )
    # check if user already exists
    if accounts_collection.get_account_by_username(new_user.get_username()):
        raise HTTPException(
            status_code=400, detail="User already exists")

    # add user to collection
    accounts_collection.add_account(new_user)

    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.get_username()}, expires_delta=access_token_expires
    )

    return JSONResponse(
        status_code=201,
        content={
            "detail": "User created successfully"
        },
        headers={
            "Authorization": access_token,
        })


@ router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    '''
    # Login a user

    ### request body (form-encoded)
    - username: `str`
    - password: `str`
    '''

    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.get_username()}, expires_delta=access_token_expires
    )
    return JSONResponse(
        status_code=200,
        content={
            "detail": "User logged in successfully"
        },
        headers={
            "Authorization": access_token,
        })
