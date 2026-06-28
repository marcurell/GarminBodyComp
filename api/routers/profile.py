from fastapi import APIRouter, Depends
from api.dependencies import get_current_user
from api.schemas.profile import ProfileResponse, ProfileUpdate
from modules.storage import load_profile, save_profile

router = APIRouter(tags=["Profile"])


@router.get("/me", response_model=ProfileResponse)
def get_profile(user_id: str = Depends(get_current_user)):
    profile = load_profile(user_id)
    return ProfileResponse(
        user_id=user_id,
        height_cm=profile.get("height", 180),
        gender=profile.get("gender", "Man"),
    )


@router.put("/me", response_model=ProfileResponse)
def update_profile(body: ProfileUpdate, user_id: str = Depends(get_current_user)):
    save_profile(user_id, {"height": body.height_cm, "gender": body.gender})
    return ProfileResponse(user_id=user_id, height_cm=body.height_cm, gender=body.gender)
