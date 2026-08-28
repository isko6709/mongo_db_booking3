from mysite.clients.auth_service import verify_access_token
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]):
    if credentials is None:
        raise HTTPException(status_code=401, detail='Не были предоставлены учетные данные для проверки подлинности')

    elif credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=401, detail='Используйте Bearer accsess token')

    return await verify_access_token(credentials.credentials)
