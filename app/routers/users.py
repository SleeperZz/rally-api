from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from ..databases import accounts_collection
from ..dependencies import get_current_user, User, check_admin_role, Admin

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={
        404: {
            'message': 'Not Found'
        }
    }
)


@router.get('/', status_code=status.HTTP_200_OK)
async def read_users(isAdmin: Annotated[bool, Depends(check_admin_role)]):
    '''
    # Get all users
    '''

    return [
        {
            'id': user.get_id(),
            'username': user.get_username(),
            'email': user.get_email()
        }
        for user in accounts_collection.get_accounts()
    ]


@router.get('/profile', status_code=status.HTTP_200_OK)
async def read_profile(current_user: Annotated[User | Admin, Depends(get_current_user)]):
    '''
    # Get profile
    '''
    return {
        'id': current_user.get_id(),
        'username': current_user.get_username(),
        'email': current_user.get_email(),
        'is_admin': isinstance(current_user, Admin)
    }


@router.get('/profile/{username}', status_code=status.HTTP_200_OK)
async def read_profile_by_username(username: str):
    '''
    # Get profile by username
    '''
    user_exists = accounts_collection.get_account_by_username(username)

    if user_exists is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        'id': user_exists.get_id(),
        'username': user_exists.get_username(),
        'email': user_exists.get_email(),
    }
