"""
标准库 Service — 业务逻辑层

所有查询强制注入 tenant_id 过滤（规范红线第 3 条）。
"""
from typing import Optional
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.standard import StdDocument, StdClause
from app.schemas.standard import (
    StdDocumentCreate,
    StdDocumentUpdate,
    StdClauseCreate,
    StdClauseUpdate,
    StdClauseTree,
)


class StandardService:
    """标准化基础库 CRUD 服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========== 规范文档 ==========

    async def list_documents(
        self,
        tenant_id: int,
        page: int = 1,
        page_size: int = 20,
        doc_type: Optional[str] = None,
        title: Optional[str] = None,
        is_current: Optional[bool] = None,
    ) -> tuple[list[dict], int]:
        """分页查询规范文档列表

        Returns:
            (items, total) — 文档列表 + 总数
        """
        # 基础查询 — 强制 tenant_id 隔离
        query = select(StdDocument).where(StdDocument.tenant_id == tenant_id)

        # 筛选条件
        if doc_type:
            query = query.where(StdDocument.doc_type == doc_type)
        if title:
            query = query.where(StdDocument.title.ilike(f"%{title}%"))
        if is_current is not None:
            query = query.where(StdDocument.is_current == is_current)

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        query = query.order_by(StdDocument.id.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(query)
        documents = result.scalars().all()

        # 聚合条款数量
        items = []
        for doc in documents:
            clause_count_result = await self.session.execute(
                select(func.count()).where(StdClause.document_id == doc.id)
            )
            clause_count = clause_count_result.scalar() or 0
            items.append({
                **{c.key: getattr(doc, c.key) for c in doc.__table__.columns},
                "clause_count": clause_count,
            })

        return items, total

    async def create_document(
        self,
        data: StdDocumentCreate,
        tenant_id: int,
        created_by: int,
    ) -> StdDocument:
        """新建规范文档"""
        doc = StdDocument(
            title=data.title,
            doc_type=data.doc_type,
            version=data.version,
            publish_date=data.publish_date,
            file_url=data.file_url,
            tenant_id=tenant_id,
            created_by=created_by,
        )
        self.session.add(doc)
        await self.session.flush()
        await self.session.refresh(doc)
        return doc

    async def get_document(self, doc_id: int, tenant_id: int) -> Optional[StdDocument]:
        """获取单个文档（含 tenant_id 隔离）"""
        result = await self.session.execute(
            select(StdDocument).where(
                StdDocument.id == doc_id,
                StdDocument.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_document(
        self,
        doc_id: int,
        tenant_id: int,
        data: StdDocumentUpdate,
    ) -> Optional[StdDocument]:
        """更新文档基础信息"""
        doc = await self.get_document(doc_id, tenant_id)
        if not doc:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(doc, key, value)
        await self.session.flush()
        await self.session.refresh(doc)
        return doc

    async def delete_document(self, doc_id: int, tenant_id: int) -> bool:
        """删除文档（级联删除所有条款）"""
        doc = await self.get_document(doc_id, tenant_id)
        if not doc:
            return False
        # 级联删除条款
        await self.session.execute(
            delete(StdClause).where(StdClause.document_id == doc_id)
        )
        await self.session.delete(doc)
        await self.session.flush()
        return True

    # ========== 条款管理 ==========

    async def get_clause_tree(self, doc_id: int) -> list[StdClauseTree]:
        """获取文档的条款树（递归构建）"""
        result = await self.session.execute(
            select(StdClause)
            .where(StdClause.document_id == doc_id)
            .order_by(StdClause.level, StdClause.id)
        )
        all_clauses = result.scalars().all()

        # 构建树形结构
        clause_map: dict[int, StdClauseTree] = {}
        roots: list[StdClauseTree] = []

        for clause in all_clauses:
            node = StdClauseTree(
                id=clause.id,
                clause_no=clause.clause_no,
                title=clause.title,
                content=clause.content,
                level=clause.level,
                children=[],
            )
            clause_map[clause.id] = node

        for clause in all_clauses:
            node = clause_map[clause.id]
            if clause.parent_id and clause.parent_id in clause_map:
                clause_map[clause.parent_id].children.append(node)
            else:
                roots.append(node)

        return roots

    async def create_clause(
        self,
        doc_id: int,
        data: StdClauseCreate,
    ) -> StdClause:
        """新增条款"""
        clause = StdClause(
            document_id=doc_id,
            parent_id=data.parent_id,
            clause_no=data.clause_no,
            title=data.title,
            content=data.content,
            level=data.level,
        )
        self.session.add(clause)
        await self.session.flush()
        await self.session.refresh(clause)
        return clause

    async def update_clause(
        self,
        clause_id: int,
        data: StdClauseUpdate,
        tenant_id: int = 0,
    ) -> Optional[StdClause]:
        """更新条款 — 必须校验条款所属文档的 tenant_id"""
        result = await self.session.execute(
            select(StdClause)
            .join(StdDocument, StdClause.document_id == StdDocument.id)
            .where(StdClause.id == clause_id, StdDocument.tenant_id == tenant_id)
        )
        clause = result.scalar_one_or_none()
        if not clause:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(clause, key, value)
        await self.session.flush()
        await self.session.refresh(clause)
        return clause

    async def delete_clause(self, clause_id: int, tenant_id: int = 0) -> bool:
        """删除条款（递归删除子条款）— 必须校验 tenant_id"""
        result = await self.session.execute(
            select(StdClause)
            .join(StdDocument, StdClause.document_id == StdDocument.id)
            .where(StdClause.id == clause_id, StdDocument.tenant_id == tenant_id)
        )
        clause = result.scalar_one_or_none()
        if not clause:
            return False

        # 递归删除子条款
        await self._delete_children(clause_id)
        await self.session.delete(clause)
        await self.session.flush()
        return True

    async def _delete_children(self, parent_id: int):
        """递归删除所有子条款"""
        result = await self.session.execute(
            select(StdClause).where(StdClause.parent_id == parent_id)
        )
        children = result.scalars().all()
        for child in children:
            await self._delete_children(child.id)
            await self.session.delete(child)
