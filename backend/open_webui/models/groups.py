import json
import logging
import time
from typing import Optional, List
import uuid

from open_webui.internal.db import Base, get_db
from open_webui.env import SRC_LOG_LEVELS

from open_webui.models.files import FileMetadataResponse


from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, JSON, func
from sqlalchemy.exc import SQLAlchemyError


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# UserGroup DB Schema
####################


class Group(Base):
    __tablename__ = "group"

    id = Column(Text, unique=True, primary_key=True)
    user_id = Column(Text)

    name = Column(Text)
    description = Column(Text)

    data = Column(JSON, nullable=True)
    meta = Column(JSON, nullable=True)

    permissions = Column(JSON, nullable=True)
    user_ids = Column(JSON, nullable=True)

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class GroupModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str

    name: str
    description: str

    data: Optional[dict] = None
    meta: Optional[dict] = None

    permissions: Optional[dict] = None
    user_ids: Optional[List[str]] = []

    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch

    @classmethod
    def model_validate(cls, group):
        group_dict = group.__dict__.copy()
        if group_dict['user_ids'] is None:
            group_dict['user_ids'] = []
        return cls(**group_dict)


####################
# Forms
####################


class GroupResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: str
    permissions: Optional[dict] = None
    data: Optional[dict] = None
    meta: Optional[dict] = None
    user_ids: list[str] = []
    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch


class GroupForm(BaseModel):
    name: str
    description: str


class GroupUpdateForm(GroupForm):
    permissions: Optional[dict] = None
    user_ids: Optional[list[str]] = None
    admin_ids: Optional[list[str]] = None


class GroupTable:
    def insert_new_group(
        self, user_id: str, form_data: GroupForm
    ) -> Optional[GroupModel]:
        with get_db() as db:
            group = GroupModel(
                **{
                    **form_data.model_dump(),
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )

            try:
                result = Group(**group.model_dump())
                db.add(result)
                db.commit()
                db.refresh(result)
                if result:
                    return GroupModel.model_validate(result)
                else:
                    return None

            except Exception:
                return None

    def get_groups(self) -> list[GroupModel]:
        with get_db() as db:
            return [
                GroupModel.model_validate(group)
                for group in db.query(Group).order_by(Group.updated_at.desc()).all()
            ]

    def get_groups_by_member_id(self, user_id: str) -> list[GroupModel]:
        with get_db() as db:
            return [
                GroupModel.model_validate(group)
                for group in db.query(Group)
                .filter(
                    func.json_array_length(Group.user_ids) > 0
                )  # Ensure array exists
                .filter(
                    Group.user_ids.cast(String).like(f'%"{user_id}"%')
                )  # String-based check
                .order_by(Group.updated_at.desc())
                .all()
            ]

    def get_group_by_id(self, id: str) -> Optional[GroupModel]:
        try:
            with get_db() as db:
                group = db.query(Group).filter_by(id=id).first()
                return GroupModel.model_validate(group) if group else None
        except Exception:
            return None

    def get_group_user_ids_by_id(self, id: str) -> Optional[str]:
        group = self.get_group_by_id(id)
        if group:
            return group.user_ids
        else:
            return None

    def update_group_by_id(
        self, id: str, form_data: GroupUpdateForm, overwrite: bool = False
    ) -> Optional[GroupModel]:
        try:
            with get_db() as db:
                db.query(Group).filter_by(id=id).update(
                    {
                        **form_data.model_dump(exclude_none=True),
                        "updated_at": int(time.time()),
                    }
                )
                db.commit()
                return self.get_group_by_id(id=id)
        except Exception as e:
            log.exception(e)
            return None

    def delete_group_by_id(self, id: str) -> bool:
        try:
            with get_db() as db:
                db.query(Group).filter_by(id=id).delete()
                db.commit()
                return True
        except Exception:
            return False

    def delete_all_groups(self) -> bool:
        with get_db() as db:
            try:
                db.query(Group).delete()
                db.commit()

                return True
            except Exception:
                return False

Groups = GroupTable()

class GroupService:
    def get_group_by_id(self, id: str) -> Optional[GroupModel]:
        try:
            with get_db() as db:
                group = db.query(Group).filter_by(id=id).first()
                return GroupModel.model_validate(group) if group else None
        except Exception:
            return None
    
    def update_group_by_id(self, id: str, form_data: GroupUpdateForm) -> Optional[GroupModel]:
        try:
            with get_db() as db:
                update_data = form_data.dict(exclude_unset=True)
                db.query(Group).filter_by(id=id).update(
                    {
                        **update_data,
                        "updated_at": int(time.time()),
                    }
                )
                db.commit()
                return self.get_group_by_id(id=id)
            return None
        except SQLAlchemyError as e:
            log.error(f"Error updating group {id}: {e}")
            return None

    def get_group_id_by_name(self, name: str) -> Optional[str]:
        try:
            with get_db() as db:
                group = db.query(Group).filter_by(name=name).first()
                return group.id if group else None
        except SQLAlchemyError as e:
            log.error(f"Error fetching group by name {name}: {e}")
            return None

    def add_user_to_group(self, group_id: str, user_id: str) -> bool:
        try:
            with get_db() as db:
                group = db.query(Group).filter_by(id=group_id).first()
                if group:
                    log.info(f"Current user_ids type: {type(group.user_ids)}")
                    log.info(f"Current user_ids: {group.user_ids}")
                    if group.user_ids is None:
                        group.user_ids = []
                    if user_id not in group.user_ids:
                        group.user_ids.append(user_id)
                        db.query(Group).filter_by(id=group_id).update(
                            {
                                "user_ids": group.user_ids,
                                "updated_at": int(time.time()),
                            }
                        )
                        db.commit()
                        db.refresh(group)
                        log.info(f"Post-commit user_ids: {group.user_ids}")
                        return True
                    else:
                        log.warning(f"User {user_id} already in group {group_id}")
                else:
                    log.warning(f"Group {group_id} not found")
                return False
        except SQLAlchemyError as e:
            log.error(f"Error adding user {user_id} to group {group_id}: {e}")
            return False

    def remove_user_from_group(self, group_id: str, user_id: str) -> bool:
        try:
            with get_db() as db:
                group = db.query(Group).filter_by(id=group_id).first()
                if group:
                    log.info(f"Current user_ids type: {type(group.user_ids)}")
                    log.info(f"Current user_ids: {group.user_ids}")
                    if group.user_ids is None:
                        group.user_ids = []
                    if user_id in group.user_ids:
                        group.user_ids.remove(user_id)
                        db.query(Group).filter_by(id=group_id).update(
                            {
                                "user_ids": group.user_ids,
                                "updated_at": int(time.time()),
                            }
                        )
                        db.commit()
                        db.refresh(group)
                        log.info(f"Post-commit user_ids: {group.user_ids}")
                        return True
                    else:
                        log.warning(f"User {user_id} not in group {group_id}")
                else:
                    log.warning(f"Group {group_id} not found")
                return False
        except SQLAlchemyError as e:
            log.error(f"Error removing user {user_id} to group {group_id}: {e}")
            return False