"""
系统管理 Service — 业务逻辑层

覆盖用户、角色、矿井、操作日志、数据字典五个子模块。
所有查询强制注入 tenant_id 过滤（规范红线第 3 条）。
"""
from typing import Optional

import bcrypt
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import SysUser, SysRole
from app.models.mine import SysMine
from app.models.audit_log import AuditLog
from app.models.dict_item import SysDictItem
from app.schemas.system import (
    UserCreate, UserUpdate, PasswordReset,
    RoleCreate, RoleUpdate,
    MineCreate, MineUpdate,
    DictItemCreate, DictItemUpdate,
)


# ========== 用户管理 ==========

class UserService:
    """用户管理 CRUD"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_users(
        self,
        tenant_id: int,
        page: int = 1,
        page_size: int = 20,
        username: Optional[str] = None,
    ) -> tuple[list[SysUser], int]:
        """分页查询用户列表"""
        query = select(SysUser).where(SysUser.tenant_id == tenant_id)
        if username:
            query = query.where(SysUser.username.ilike(f"%{username}%"))

        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_q)).scalar() or 0

        query = query.order_by(SysUser.id.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        users = list((await self.session.execute(query)).scalars().all())
        return users, total

    async def create_user(
        self, data: UserCreate, tenant_id: int, created_by: int
    ) -> SysUser:
        """新增用户"""
        # 检查用户名唯一
        existing = (await self.session.execute(
            select(SysUser).where(SysUser.username == data.username)
        )).scalar_one_or_none()
        if existing:
            raise ValueError(f"用户名 '{data.username}' 已存在")

        hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
        user = SysUser(
            username=data.username,
            hashed_password=hashed,
            real_name=data.real_name,
            role_id=data.role_id,
            is_active=data.is_active,
            tenant_id=tenant_id,
            created_by=created_by,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_user(
        self, user_id: int, tenant_id: int, data: UserUpdate
    ) -> Optional[SysUser]:
        """更新用户信息"""
        user = await self._get_user(user_id, tenant_id)
        if not user:
            return None
        update = data.model_dump(exclude_unset=True)
        for k, v in update.items():
            setattr(user, k, v)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def toggle_active(self, user_id: int, tenant_id: int) -> Optional[SysUser]:
        """切换用户启用/禁用状态"""
        user = await self._get_user(user_id, tenant_id)
        if not user:
            return None
        user.is_active = not user.is_active
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def reset_password(
        self, user_id: int, tenant_id: int, data: PasswordReset
    ) -> bool:
        """重置用户密码"""
        user = await self._get_user(user_id, tenant_id)
        if not user:
            return False
        hashed = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
        user.hashed_password = hashed
        await self.session.flush()
        return True

    async def _get_user(self, user_id: int, tenant_id: int) -> Optional[SysUser]:
        result = await self.session.execute(
            select(SysUser).where(SysUser.id == user_id, SysUser.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()


# ========== 角色管理 ==========

class RoleService:
    """角色管理 CRUD"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_roles(self, tenant_id: int) -> list[SysRole]:
        """获取角色列表"""
        result = await self.session.execute(
            select(SysRole).where(SysRole.tenant_id == tenant_id).order_by(SysRole.id)
        )
        return list(result.scalars().all())

    async def create_role(
        self, data: RoleCreate, tenant_id: int, created_by: int
    ) -> SysRole:
        """新增角色"""
        role = SysRole(
            name=data.name,
            description=data.description,
            tenant_id=tenant_id,
            created_by=created_by,
        )
        self.session.add(role)
        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def update_role(self, role_id: int, tenant_id: int, data: RoleUpdate) -> Optional[SysRole]:
        """编辑角色"""
        role = await self._get_role(role_id, tenant_id)
        if not role:
            return None
        update = data.model_dump(exclude_unset=True)
        for k, v in update.items():
            setattr(role, k, v)
        await self.session.flush()
        await self.session.refresh(role)
        return role

    async def delete_role(self, role_id: int, tenant_id: int) -> bool:
        """删除角色（关联用户的 role_id 会被置空）"""
        role = await self._get_role(role_id, tenant_id)
        if not role:
            return False
        await self.session.delete(role)
        await self.session.flush()
        return True

    async def _get_role(self, role_id: int, tenant_id: int) -> Optional[SysRole]:
        result = await self.session.execute(
            select(SysRole).where(SysRole.id == role_id, SysRole.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()


# ========== 矿井配置 ==========

class MineService:
    """矿井管理 CRUD"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_mines(
        self, tenant_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[SysMine], int]:
        """分页查询矿井列表"""
        query = select(SysMine).where(SysMine.tenant_id == tenant_id)
        total = (await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )).scalar() or 0

        mines = list((await self.session.execute(
            query.order_by(SysMine.id.desc()).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all())
        return mines, total

    async def create_mine(
        self, data: MineCreate, tenant_id: int, created_by: int
    ) -> SysMine:
        """新增矿井"""
        mine = SysMine(
            name=data.name, company=data.company, gas_level=data.gas_level,
            address=data.address, contact=data.contact, phone=data.phone,
            tenant_id=tenant_id, created_by=created_by,
        )
        self.session.add(mine)
        await self.session.flush()
        await self.session.refresh(mine)
        return mine

    async def update_mine(
        self, mine_id: int, tenant_id: int, data: MineUpdate
    ) -> Optional[SysMine]:
        """编辑矿井"""
        mine = await self._get_mine(mine_id, tenant_id)
        if not mine:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(mine, k, v)
        await self.session.flush()
        await self.session.refresh(mine)
        return mine

    async def delete_mine(self, mine_id: int, tenant_id: int) -> bool:
        """删除矿井"""
        mine = await self._get_mine(mine_id, tenant_id)
        if not mine:
            return False
        await self.session.delete(mine)
        await self.session.flush()
        return True

    async def _get_mine(self, mine_id: int, tenant_id: int) -> Optional[SysMine]:
        result = await self.session.execute(
            select(SysMine).where(SysMine.id == mine_id, SysMine.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()


# ========== 操作日志 ==========

class AuditLogService:
    """操作审计日志服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_logs(
        self,
        tenant_id: int,
        page: int = 1,
        page_size: int = 20,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        username: Optional[str] = None,
    ) -> tuple[list[AuditLog], int]:
        """分页查询操作日志"""
        query = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
        if action:
            query = query.where(AuditLog.action == action)
        if resource:
            query = query.where(AuditLog.resource == resource)
        if username:
            query = query.where(AuditLog.username.ilike(f"%{username}%"))

        total = (await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )).scalar() or 0

        logs = list((await self.session.execute(
            query.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all())
        return logs, total

    @staticmethod
    async def log_action(
        session: AsyncSession,
        user_id: int,
        username: str,
        action: str,
        resource: str,
        tenant_id: int,
        detail: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """记录一条操作日志（工具方法，可在任何路由中调用）"""
        log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource=resource,
            detail=detail,
            ip_address=ip_address,
            tenant_id=tenant_id,
        )
        session.add(log)
        await session.flush()


# ========== 数据字典 ==========

class DictService:
    """数据字典管理"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_by_type(
        self, tenant_id: int, dict_type: Optional[str] = None
    ) -> list[SysDictItem]:
        """按类型获取字典项列表"""
        query = select(SysDictItem).where(SysDictItem.tenant_id == tenant_id)
        if dict_type:
            query = query.where(SysDictItem.dict_type == dict_type)
        query = query.order_by(SysDictItem.dict_type, SysDictItem.sort_order, SysDictItem.id)
        return list((await self.session.execute(query)).scalars().all())

    async def get_dict_types(self, tenant_id: int) -> list[str]:
        """获取所有字典类型列表"""
        result = await self.session.execute(
            select(SysDictItem.dict_type)
            .where(SysDictItem.tenant_id == tenant_id)
            .distinct()
            .order_by(SysDictItem.dict_type)
        )
        return [r[0] for r in result.all()]

    async def create_item(
        self, data: DictItemCreate, tenant_id: int, created_by: int
    ) -> SysDictItem:
        """新增字典项"""
        item = SysDictItem(
            dict_type=data.dict_type, dict_key=data.dict_key,
            dict_value=data.dict_value, sort_order=data.sort_order,
            is_active=data.is_active,
            tenant_id=tenant_id, created_by=created_by,
        )
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def update_item(
        self, item_id: int, tenant_id: int, data: DictItemUpdate
    ) -> Optional[SysDictItem]:
        """编辑字典项"""
        item = await self._get_item(item_id, tenant_id)
        if not item:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(item, k, v)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def delete_item(self, item_id: int, tenant_id: int) -> bool:
        """删除字典项"""
        item = await self._get_item(item_id, tenant_id)
        if not item:
            return False
        await self.session.delete(item)
        await self.session.flush()
        return True

    async def _get_item(self, item_id: int, tenant_id: int) -> Optional[SysDictItem]:
        result = await self.session.execute(
            select(SysDictItem).where(
                SysDictItem.id == item_id, SysDictItem.tenant_id == tenant_id
            )
        )
        return result.scalar_one_or_none()
