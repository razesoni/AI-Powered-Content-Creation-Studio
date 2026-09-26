from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.llm.content_generation import IdeaGenerationError, OutlineGenerationError, DraftGenerationError, ImageGenerationError
from core.config import get_settings
from core.security import create_access_token, decode_access_token
from backend.database.db_schema import User
from backend.database.db_store import (create_project, delete_user_project, get_db, get_project_drafts, get_project_images,
                            get_project_ideas, get_project_outlines,get_user_projects,save_generated_ideas,save_generated_images,
                            save_generated_outlines,save_generated_drafts,login_user,register_user, IdempotencyKeyReuseError)

from server.schema.user_schema import (DraftResponse,GenerateDraft,ImageResponse,GenerateImage,IdeaResponse,LoginUser,NewProject,
                                    GenerateIdeas,GenerateOutline,OutlineResponse,ProjectResponse,RegisterUser,Token,UserResponse)

settings = get_settings()
app = FastAPI(title="AI-Powered Content Creation Studio API", version="0.1.0")
image_storage_dir = Path(settings.image_storage_dir).resolve()
image_storage_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    settings.image_public_path,
    StaticFiles(directory=image_storage_dir),
    name="generated-images",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
BearerToken = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(token: BearerToken, db: DatabaseSession) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = UUID(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        raise unauthorized from None

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise unauthorized
    return user


@app.get("/")
def read_root():
    return {"message": "Welcome to the AI-Powered Content Creation Studio API"}


@app.post("/api/v1/auth/register", response_model=UserResponse, status_code=201)
@app.post("/register", response_model=UserResponse, status_code=201, include_in_schema=False)
async def register(request: RegisterUser, db: DatabaseSession):
    try:
        user = await register_user(request, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not user:
        raise HTTPException(status_code=409, detail="User already registered")
    return user

@app.post("/api/v1/auth/login", response_model=Token)
@app.post("/login", response_model=Token, include_in_schema=False)
async def login(request: LoginUser, db: DatabaseSession):
    try:
        user = await login_user(request, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(str(user.id)))


@app.get("/api/v1/users/me", response_model=UserResponse)
async def read_current_user(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@app.post("/api/v1/projects", response_model=ProjectResponse, status_code=201)
@app.post("/api/v1/users/me/new_project",response_model=ProjectResponse,status_code=201,include_in_schema=False)
@app.post("/new_project", response_model=ProjectResponse, status_code=201, include_in_schema=False)
async def new_project(p: NewProject, current_user: Annotated[User, Depends(get_current_user)], db: DatabaseSession):    
    project = await create_project(p, current_user.id, db)
    return project


@app.get("/api/v1/projects", response_model=list[ProjectResponse])
async def list_projects(current_user: Annotated[User, Depends(get_current_user)], db: DatabaseSession):
    projects = await get_user_projects(current_user.id, db)
    return projects


@app.delete("/api/v1/projects/{project_id}", status_code=204)
async def delete_project(project_id: UUID, current_user: Annotated[User, Depends(get_current_user)], db: DatabaseSession):
    deleted = await delete_user_project(project_id, current_user.id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")


@app.post("/api/v1/projects/{project_id}/ideas/generate", response_model=list[IdeaResponse], status_code=201)
@app.post("/api/v1/projects/{project_id}/generate_ideas", response_model=list[IdeaResponse], status_code=201, include_in_schema=False)
async def generate_ideas_endpoint(idea_des: GenerateIdeas, project_id: UUID, current_user: Annotated[User, Depends(get_current_user)], db: DatabaseSession,):
    try:
        ideas = await save_generated_ideas(idea_des, project_id, current_user.id, db, idea_des.idempotency_key)
    except IdeaGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except IdempotencyKeyReuseError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if ideas is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ideas


@app.get("/api/v1/projects/{project_id}/ideas", response_model=list[IdeaResponse])
async def list_ideas(project_id: UUID, current_user: Annotated[User, Depends(get_current_user)], db: DatabaseSession,):
    ideas = await get_project_ideas(project_id, current_user.id, db)
    if ideas is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ideas


@app.post("/api/v1/projects/{project_id}/outlines/generate",response_model=OutlineResponse,status_code=201)
async def generate_outlines_endpoint(project_id: UUID, request: GenerateOutline, current_user: Annotated[User, Depends(get_current_user)],db: DatabaseSession,):
    try:
        outlines = await save_generated_outlines(request.idea_id, project_id, current_user.id, db, request.idempotency_key)
    except OutlineGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except IdempotencyKeyReuseError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if outlines is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return outlines


@app.get("/api/v1/projects/{project_id}/outlines", response_model=list[OutlineResponse])
async def list_outlines(project_id: UUID,current_user: Annotated[User, Depends(get_current_user)],db: DatabaseSession):
    outlines = await get_project_outlines(project_id, current_user.id, db)
    if outlines is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return outlines

@app.post("/api/v1/projects/{project_id}/drafts/generate",status_code=201,response_model=DraftResponse)
async def generate_draft_from_frontend(project_id: UUID,request: GenerateDraft,current_user: Annotated[User, Depends(get_current_user)],db: DatabaseSession):
    try:
        draft = await save_generated_drafts(request.outline_id,project_id,current_user.id,db,draft_format=request.format,instructions=request.instructions,idempotency_key=request.idempotency_key)
    except DraftGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except IdempotencyKeyReuseError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if draft is None:
        raise HTTPException(status_code=404, detail="Project, idea, or outline not found")
    return draft

@app.get("/api/v1/projects/{project_id}/drafts", response_model=list[DraftResponse])
async def list_drafts(project_id: UUID,current_user: Annotated[User, Depends(get_current_user)],db: DatabaseSession):
    drafts = await get_project_drafts(project_id, current_user.id, db)
    if drafts is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return drafts

@app.post(
    "/api/v1/projects/{project_id}/images/generate",
    status_code=201,
    response_model=list[ImageResponse],
)
async def generate_images_endpoint(
    project_id: UUID,
    request: GenerateImage,
    current_user: Annotated[User, Depends(get_current_user)],
    db: DatabaseSession,
):
    try:
        images = await save_generated_images(request.draft_id,project_id,current_user.id,db,style=request.style,image_count=request.image_count,aspect_ratio=request.aspect_ratio,prompt=request.prompt,idempotency_key=request.idempotency_key)
    except ImageGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except IdempotencyKeyReuseError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if images is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return images
        
@app.get("/api/v1/projects/{project_id}/images", response_model=list[ImageResponse])
async def list_images(project_id: UUID,current_user: Annotated[User, Depends(get_current_user)],db: DatabaseSession):
    images = await get_project_images(project_id, current_user.id, db)
    if images is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return images


@app.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"code": "internal_error", "message": "Unexpected server error"},
    )
