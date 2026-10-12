import time
import datetime
from typing import Optional, List, Callable
import jwt
from jwt import PyJWKClient, PyJWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.models.schemas import UserPrincipal

security = HTTPBearer(auto_error=False)

# Role hierarchy
ROLE_HIERARCHY = {
    "admin": ["admin", "operator", "viewer"],
    "operator": ["operator", "viewer"],
    "viewer": ["viewer"]
}

def create_demo_token(username: str, role: str) -> str:
    """Issue a signed JWT for local demo/testing mode only."""
    if not settings.demo_mode or settings.environment.lower() == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo token creation is prohibited in production or when demo mode is disabled."
        )
    
    roles = ROLE_HIERARCHY.get(role, [role])
    payload = {
        "sub": f"demo-{username}",
        "preferred_username": username,
        "email": f"{username}@local.dev",
        "realm_access": {"roles": roles},
        "iss": "demo-authority",
        "aud": settings.oidc_audience,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "is_demo": True
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def decode_token(token: str) -> UserPrincipal:
    """Validate and decode JWT bearer token."""
    # First check if demo token
    try:
        unverified = jwt.decode(token, options={"verify_signature": False})
        if unverified.get("is_demo") is True:
            if not settings.demo_mode or settings.environment.lower() == "production":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Demo tokens rejected: demo mode disabled or running in production."
                )
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=["HS256"],
                audience=settings.oidc_audience
            )
            roles = payload.get("realm_access", {}).get("roles", [])
            return UserPrincipal(
                sub=payload.get("sub", "unknown"),
                username=payload.get("preferred_username", "demo-user"),
                email=payload.get("email"),
                roles=roles,
                is_demo=True
            )
    except PyJWTError:
        pass

    # Real Keycloak OIDC verification
    jwks_url = f"{settings.oidc_issuer_url.rstrip('/')}/protocol/openid-connect/certs"
    try:
        jwks_client = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=3600)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.oidc_issuer_url,
            audience=settings.oidc_audience,
            options={"verify_exp": True}
        )
        roles = payload.get("realm_access", {}).get("roles", [])
        return UserPrincipal(
            sub=payload.get("sub", ""),
            username=payload.get("preferred_username", payload.get("sub", "")),
            email=payload.get("email"),
            roles=roles,
            is_demo=False
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> UserPrincipal:
    if not creds or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return decode_token(creds.credentials)

def require_role(required_role: str) -> Callable[[UserPrincipal], UserPrincipal]:
    def dependency(user: UserPrincipal = Depends(get_current_user)) -> UserPrincipal:
        user_roles = set(user.roles)
        # Check direct or inherited role permissions
        has_permission = False
        for r in user_roles:
            if required_role in ROLE_HIERARCHY.get(r, [r]):
                has_permission = True
                break
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: requires '{required_role}' role"
            )
        return user
    return dependency
