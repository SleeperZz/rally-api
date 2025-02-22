from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
from ..databases import landmarks_collection, accounts_collection
from ..internal.review import Review
from ..dependencies import get_current_user, User


router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
    responses={
        404: {
            'message': 'Not Found'
        }
    },
    dependencies=[Depends(get_current_user)]
)


@router.get('/',  status_code=status.HTTP_200_OK)
async def read_reviews(user: str | None = None):
    '''
    # get all reviews
    '''

    if user:
        user_exists = accounts_collection.get_account_by_username(user)
        if not user_exists:
            raise HTTPException(status_code=404, detail="User not found")

        user_reviews = []

        for landmark in landmarks_collection.get_landmarks():
            for review in landmark.get_reviews():
                if review.get_reviewer() == user:
                    user_reviews.append({
                        "id": review.get_id(),
                        "reviewer": review.get_reviewer(),
                        "review_text": review.get_review_text(),
                        "rating": review.get_rating(),
                        "landmark_id": landmark.get_id(),
                        "landmark_name": landmark.get_name()
                    })

        return user_reviews

    return [{
        "id": review.get_id(),
        "reviewer": review.get_reviewer(),
        "review_text": review.get_review_text(),
        "rating": review.get_rating(),
        "landmark_id": landmark.get_id(),
        "landmark_name": landmark.get_name()
    } for landmark in landmarks_collection.get_landmarks() for review in landmark.get_reviews()]


@router.post('/')
async def create_review(body: dict, current_user: Annotated[User, Depends(get_current_user)]):
    '''
    # create new review
    '''

    if not body:
        raise HTTPException(status_code=400, detail="Bad request")

    landmark_exists = landmarks_collection.get_landmark_by_id(
        body.get('landmark_id'))

    if not landmark_exists:
        raise HTTPException(status_code=404, detail="Landmark not found")

    review_exists = landmark_exists.get_review_by_username(
        current_user.get_username())

    if review_exists:
        raise HTTPException(status_code=400, detail="Review already exists")

    review = Review(
        reviewer=current_user.get_username(),
        review_text=body.get('review_text'),
        rating=body.get('rating')
    )

    landmark_exists.add_review(review)

    return {
        'detail': 'Review created'
    }


@router.patch("/{review_id}")
async def edit_review(review_id, body: dict, current_user: Annotated[User, Depends(get_current_user)]):
    '''
    # edit review    
    '''

    if not body:
        raise HTTPException(status_code=400, detail="Bad request")

    landmark = landmarks_collection.get_landmark_by_review_id(review_id)
    if not landmark:
        raise HTTPException(404, "Review not found")

    review = landmark.get_review_by_id(review_id)

    if review.get_reviewer() != current_user.get_username():
        raise HTTPException(403, "Forbidden")

    review.set_review_text(body.get('review_text', review.get_review_text()))
    review.set_rating(body.get('rating', review.get_rating()))

    return {
        'detail': 'Review edited'
    }


@router.delete("/{review_id}")
async def delete_review(review_id: str, current_user: Annotated[User, Depends(get_current_user)]):
    '''
    # delete review
    '''

    landmark = landmarks_collection.get_landmark_by_review_id(review_id)
    if not landmark:
        raise HTTPException(404, "Review not found")

    review = landmark.get_review_by_id(review_id)

    if review.get_reviewer() != current_user.get_username():
        raise HTTPException(403, "Forbidden")

    landmark.remove_review(review)

    return {
        'detail': 'Review deleted'
    }
