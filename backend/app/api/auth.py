from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import settings
from app.core.auth import create_demo_token, get_current_user
from app.models.schemas import UserPrincipal, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

class DemoLoginRequest(BaseModel):
    username: str = "demo-analyst"
    role: str = "operator"

@router.post("/demo-token", response_model=TokenResponse)
def get_demo_token(payload: DemoLoginRequest):
    if not settings.demo_mode or settings.environment.lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo authentication is prohibited in production or when demo mode is disabled."
        )
    if payload.role not in {"viewer", "operator", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be one of: viewer, operator, admin"
        )
    token = create_demo_token(payload.username, payload.role)
    user = UserPrincipal(
        sub=f"demo-{payload.username}",
        username=payload.username,
        email=f"{payload.username}@local.dev",
        roles=[payload.role],
        is_demo=True
    )
    return TokenResponse(access_token=token, token_type="bearer", expires_in=3600, user=user)

@router.get("/me", response_model=UserPrincipal)
def get_profile(user: UserPrincipal = Depends(get_current_user)):
    return user

@router.post("/logout")
def logout(user: UserPrincipal = Depends(get_current_user)):
    return {"status": "logged_out", "user": user.username}

@router.get("/oidc-config")
def get_oidc_config():
    issuer = settings.oidc_issuer_url.rstrip("/")
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/protocol/openid-connect/auth",
        "token_endpoint": f"{issuer}/protocol/openid-connect/token",
        "userinfo_endpoint": f"{issuer}/protocol/openid-connect/userinfo",
        "end_session_endpoint": f"{issuer}/protocol/openid-connect/logout",
        "jwks_uri": f"{issuer}/protocol/openid-connect/certs",
        "client_id": settings.oidc_client_id,
        "response_types_supported": ["code"],
        "code_challenge_methods_supported": ["S256"],
        "demo_mode_enabled": settings.demo_mode
    }
