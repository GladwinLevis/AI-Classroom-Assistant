import uuid
from typing import List
from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, BaseModel

# Many-to-Many association table linking Roles and Permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True, index=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True, index=True)
)

# Many-to-Many association table linking Users and Roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True, index=True)
)


class Permission(BaseModel):
    """
    SQLAlchemy Model representing granular application permissions.
    Example: 'course:create', 'grade:view'.
    """
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        secondary=role_permissions,
        back_populates="permissions"
    )


class Role(BaseModel):
    """
    SQLAlchemy Model representing User Roles (e.g. Student, Teacher, Admin).
    Binds permissions to users.
    """
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    permissions: Mapped[List[Permission]] = relationship(
        secondary=role_permissions,
        back_populates="roles"
    )
    users: Mapped[List["User"]] = relationship(
        secondary=user_roles,
        back_populates="roles"
    )
