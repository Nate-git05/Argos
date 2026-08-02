from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.server.web.config.database import get_db
from application.server.web.models.users.registered_users import RegisteredUser
from application.server.web.routes import register_router
from application.server.web.schemas.registered_users import RegisterRequest, RegisterResponse


@register_router.post("", response_model=RegisterResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> RegisterResponse:
    existing = await db.scalar(select(RegisteredUser).where(RegisteredUser.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="This email is already registered.")

    user = RegisteredUser(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return RegisterResponse(id=user.id, first_name=user.first_name, last_name=user.last_name, email=user.email)
