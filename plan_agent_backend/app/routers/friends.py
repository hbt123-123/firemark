from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.orm import joinedload

from app.dependencies import get_current_user, SessionLocal
from app.models import User, Friendship, Task


class FriendRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=80, description="Username to send friend request")


class FriendResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class FriendshipResponse(BaseModel):
    id: int
    user_id: int
    friend_id: int
    friend_username: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FriendTaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    due_date: date
    due_time: Optional[str]
    status: str
    priority: int

    class Config:
        from_attributes = True


class FriendTaskListResponse(BaseModel):
    tasks: List[FriendTaskResponse]
    total: int
    friend_id: int
    friend_username: str


router = APIRouter(prefix="/friends", tags=["friends"])


@router.get("", response_model=List[FriendResponse])
async def list_friends(
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        friend_ids_subquery = (
            db.query(Friendship.friend_id)
            .filter(
                Friendship.user_id == current_user.id,
                Friendship.status == "accepted",
            )
            .union(
                db.query(Friendship.user_id)
                .filter(
                    Friendship.friend_id == current_user.id,
                    Friendship.status == "accepted",
                )
            )
            .subquery()
        )

        friends = (
            db.query(User)
            .filter(User.id.in_(friend_ids_subquery))
            .all()
        )

        return [
            FriendResponse(
                id=friend.id,
                username=friend.username,
                created_at=friend.created_at,
            )
            for friend in friends
        ]


@router.get("/requests", response_model=List[FriendshipResponse])
async def list_friend_requests(
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        requests = (
            db.query(Friendship)
            .options(joinedload(Friendship.user))
            .filter(
                Friendship.friend_id == current_user.id,
                Friendship.status == "pending",
            )
            .all()
        )

        return [
            FriendshipResponse(
                id=req.id,
                user_id=req.user_id,
                friend_id=req.friend_id,
                friend_username=req.user.username if req.user else "Unknown",
                status=req.status,
                created_at=req.created_at,
            )
            for req in requests
        ]


@router.get("/sent", response_model=List[FriendshipResponse])
async def list_sent_requests(
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        requests = (
            db.query(Friendship)
            .options(joinedload(Friendship.friend))
            .filter(
                Friendship.user_id == current_user.id,
                Friendship.status == "pending",
            )
            .all()
        )

        return [
            FriendshipResponse(
                id=req.id,
                user_id=req.user_id,
                friend_id=req.friend_id,
                friend_username=req.friend.username if req.friend else "Unknown",
                status=req.status,
                created_at=req.created_at,
            )
            for req in requests
        ]


@router.post("/request")
async def send_friend_request(
    request: FriendRequest,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        target_user = db.query(User).filter(User.username == request.username).first()

        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if target_user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send friend request to yourself",
            )

        existing = (
            db.query(Friendship)
            .filter(
                ((Friendship.user_id == current_user.id) & (Friendship.friend_id == target_user.id))
                | ((Friendship.user_id == target_user.id) & (Friendship.friend_id == current_user.id))
            )
            .first()
        )

        if existing:
            if existing.status == "accepted":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Already friends with this user",
                )
            elif existing.status == "pending":
                if existing.user_id == current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Friend request already sent",
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="This user has already sent you a friend request",
                    )

        friendship = Friendship(
            user_id=current_user.id,
            friend_id=target_user.id,
            status="pending",
        )
        db.add(friendship)
        db.commit()
        db.refresh(friendship)

        return {
            "success": True,
            "message": f"Friend request sent to {request.username}",
            "friendship_id": friendship.id,
        }


@router.post("/accept/{friendship_id}")
async def accept_friend_request(
    friendship_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        friendship = (
            db.query(Friendship)
            .filter(
                Friendship.id == friendship_id,
                Friendship.friend_id == current_user.id,
                Friendship.status == "pending",
            )
            .first()
        )

        if not friendship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Friend request not found",
            )

        friendship.status = "accepted"
        db.commit()

        return {"success": True, "message": "Friend request accepted"}


@router.delete("/reject/{friendship_id}")
async def reject_friend_request(
    friendship_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        friendship = (
            db.query(Friendship)
            .filter(
                Friendship.id == friendship_id,
                Friendship.friend_id == current_user.id,
                Friendship.status == "pending",
            )
            .first()
        )

        if not friendship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Friend request not found",
            )

        db.delete(friendship)
        db.commit()

        return {"success": True, "message": "Friend request rejected"}


@router.delete("/cancel/{friendship_id}")
async def cancel_friend_request(
    friendship_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        friendship = (
            db.query(Friendship)
            .filter(
                Friendship.id == friendship_id,
                Friendship.user_id == current_user.id,
                Friendship.status == "pending",
            )
            .first()
        )

        if not friendship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Friend request not found",
            )

        db.delete(friendship)
        db.commit()

        return {"success": True, "message": "Friend request cancelled"}


@router.delete("/{friend_id}")
async def remove_friend(
    friend_id: int,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        friendship = (
            db.query(Friendship)
            .filter(
                Friendship.status == "accepted",
                ((Friendship.user_id == current_user.id) & (Friendship.friend_id == friend_id))
                | ((Friendship.user_id == friend_id) & (Friendship.friend_id == current_user.id)),
            )
            .first()
        )

        if not friendship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Friendship not found",
            )

        db.delete(friendship)
        db.commit()

        return {"success": True, "message": "Friend removed"}


@router.get("/{friend_id}/tasks", response_model=FriendTaskListResponse)
async def get_friend_tasks(
    friend_id: int,
    due_date: Optional[date] = Query(None, description="Filter by due date"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        friendship = (
            db.query(Friendship)
            .filter(
                Friendship.status == "accepted",
                ((Friendship.user_id == current_user.id) & (Friendship.friend_id == friend_id))
                | ((Friendship.user_id == friend_id) & (Friendship.friend_id == current_user.id)),
            )
            .first()
        )

        if not friendship:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view tasks of your friends",
            )

        friend = db.query(User).filter(User.id == friend_id).first()
        if not friend:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Friend not found",
            )

        query = db.query(Task).filter(Task.user_id == friend_id)

        if due_date:
            query = query.filter(Task.due_date == due_date)
        if status_filter:
            query = query.filter(Task.status == status_filter)

        tasks = query.order_by(Task.due_date, Task.due_time).limit(50).all()

        return FriendTaskListResponse(
            tasks=[FriendTaskResponse(
                id=t.id,
                title=t.title,
                description=t.description,
                due_date=t.due_date,
                due_time=t.due_time,
                status=t.status,
                priority=t.priority,
            ) for t in tasks],
            total=len(tasks),
            friend_id=friend_id,
            friend_username=friend.username,
        )
