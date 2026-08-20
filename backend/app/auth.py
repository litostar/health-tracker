"""
极简单用户鉴权：所有 API 必须在 Header 带 Bearer Token。
适合个人项目——只有你一个人用，不需要注册/登录系统，一个口令即可。
"""
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import API_TOKEN

# auto_error=False：当请求没带 token 时，不自动报 403，而是交给我们自己返回 401
bearer = HTTPBearer(auto_error=False)


def require_token(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    """依赖函数：校验 Bearer Token，失败抛 401。"""
    if creds is None or creds.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="无效或缺失访问口令")
    return creds.credentials
