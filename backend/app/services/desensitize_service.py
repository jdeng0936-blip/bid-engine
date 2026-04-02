"""
统一脱敏网关 — 生鲜投标场景专用

核心链路：
  用户输入 → mask() → 云端 LLM → unmask() → 前端展示

设计决策：
  - 内存字典（每次生成周期独立，无需 DB 持久化）
  - 生鲜垂直领域正则：资质编号、冷链车牌、溯源码、电话、金额、地址
  - mask/unmask 双向对称，确保原始数据零泄漏

移植自 bid-engine/staging/biaobiao DesensitizeGateway，
去除 psycopg2/DB 依赖，适配 shangxianshicai 异步架构。
"""
import re
import logging
from typing import Optional

logger = logging.getLogger("desensitize_service")

# 实体类型 → 占位符前缀映射
_ENTITY_PREFIX = {
    "phone": "PHONE",
    "amount": "AMOUNT",
    "address": "ADDR",
    "license": "LICENSE",      # 资质编号（食品经营许可证/SC/HACCP等）
    "plate": "PLATE",          # 冷链车牌号
    "trace_code": "TRACE",     # 溯源码
    "person": "PERSON",        # 人员姓名
    "org": "ORG",              # 组织机构名
    "id_number": "IDNO",       # 身份证号
}

# 自动发现正则模式 — 生鲜投标场景
_PATTERNS = {
    # 手机号
    "phone": re.compile(
        r'1[3-9]\d{9}'
        r'|0\d{2,3}-?\d{7,8}'
    ),
    # 金额：¥1,234.56 / 123.45万元 / 1234元
    "amount": re.compile(
        r'(?:¥|￥)\s*[\d,]+(?:\.\d{1,2})?\s*(?:万元|亿元|元|千元)?'
        r'|[\d,]+(?:\.\d{1,2})?\s*(?:万元|亿元)'
    ),
    # 资质编号：食品经营许可证号、SC编号、各类证书编号
    "license": re.compile(
        r'JY[12]\d{12,16}'            # 食品经营许可证 JY1/JY2 + 数字
        r'|SC\d{12,14}'               # 食品生产许可证 SC + 数字
        r'|91\d{16}[0-9A-Z]'          # 统一社会信用代码
        r'|[A-Z]{2,5}\d{6,10}'        # 通用证书编号格式
    ),
    # 冷链车牌号
    "plate": re.compile(
        r'[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁]'
        r'[A-HJ-NP-Z][A-HJ-NP-Z0-9]{4,5}[A-HJ-NP-Z0-9挂学警港澳]'
    ),
    # 溯源码（纯数字长编码）
    "trace_code": re.compile(
        r'(?<!\d)\d{16,20}(?!\d)'     # 16-20位纯数字，非金额上下文
    ),
    # 身份证号
    "id_number": re.compile(
        r'[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]'
    ),
    # 地址：XX市XX区XX路XX号
    "address": re.compile(
        r'[\u4e00-\u9fa5]{2,6}(?:省|市|区|县|镇|乡|街道|路|巷|号|弄|栋|楼)'
        r'[\u4e00-\u9fa5A-Za-z0-9\-]{2,30}'
        r'(?:号|栋|楼|层|室)?'
    ),
}


class DesensitizeGateway:
    """
    统一脱敏网关（内存字典版）

    用法:
        gateway = DesensitizeGateway(tenant_id=123)
        masked_text, mapping = gateway.mask(raw_text)
        # ... 发送 masked_text 到云端 LLM ...
        final_text = gateway.unmask(llm_output, mapping)
    """

    def __init__(self, tenant_id: int = 0):
        self.tenant_id = tenant_id
        self._dict_cache: dict[str, str] = {}      # original → placeholder
        self._reverse_cache: dict[str, str] = {}    # placeholder → original
        self._counter: dict[str, int] = {}           # 每种类型的计数器

    def _get_or_create_placeholder(self, original: str, entity_type: str) -> str:
        """获取或创建占位符"""
        if original in self._dict_cache:
            return self._dict_cache[original]

        prefix = _ENTITY_PREFIX.get(entity_type, entity_type.upper())
        self._counter[entity_type] = self._counter.get(entity_type, 0) + 1
        placeholder = f"[{prefix}_{self._counter[entity_type]}]"

        self._dict_cache[original] = placeholder
        self._reverse_cache[placeholder] = original
        return placeholder

    def mask(
        self, text: str, extra_entities: Optional[dict[str, str]] = None
    ) -> tuple[str, dict[str, str]]:
        """
        脱敏：将敏感信息替换为占位符

        Args:
            text: 原始文本
            extra_entities: 额外手动指定实体 {"原文": "类型"}

        Returns:
            (脱敏后文本, 映射表 {占位符: 原文})
        """
        mapping: dict[str, str] = {}
        masked = text

        # 1. 先处理手动指定的实体（优先级最高）
        if extra_entities:
            for original, entity_type in extra_entities.items():
                if original and original in masked:
                    placeholder = self._get_or_create_placeholder(original, entity_type)
                    masked = masked.replace(original, placeholder)
                    mapping[placeholder] = original

        # 2. 用已有词典做全局替换（按长度降序，避免短匹配覆盖长匹配）
        sorted_entries = sorted(
            self._dict_cache.items(),
            key=lambda x: len(x[0]),
            reverse=True,
        )
        for original, placeholder in sorted_entries:
            if original in masked and placeholder not in mapping:
                masked = masked.replace(original, placeholder)
                mapping[placeholder] = original

        # 3. 正则自动发现新实体
        for entity_type, pattern in _PATTERNS.items():
            for match in pattern.finditer(masked):
                found = match.group().strip()
                if found.startswith("[") and found.endswith("]"):
                    continue
                if len(found) < 3:
                    continue
                placeholder = self._get_or_create_placeholder(found, entity_type)
                masked = masked.replace(found, placeholder)
                mapping[placeholder] = found

        if mapping:
            logger.info(
                f"[脱敏] tenant={self.tenant_id} | "
                f"脱敏 {len(mapping)} 项: "
                + ", ".join(f"{k}({v[:6]}...)" for k, v in list(mapping.items())[:5])
            )

        return masked, mapping

    def unmask(self, text: str, mapping: Optional[dict[str, str]] = None) -> str:
        """
        回填：将占位符替换回原始值

        Args:
            text: LLM 输出的含占位符文本
            mapping: mask() 返回的映射表
        """
        result = text

        # 优先用传入的 mapping
        if mapping:
            for placeholder, original in mapping.items():
                result = result.replace(placeholder, original)

        # 再用全局词典补充回填（覆盖 LLM 自己生成的占位符引用）
        for placeholder, original in self._reverse_cache.items():
            if placeholder in result:
                result = result.replace(placeholder, original)

        return result

    def get_stats(self) -> dict:
        """获取当前脱敏词典统计"""
        stats: dict[str, int] = {}
        for placeholder in self._dict_cache.values():
            for entity_type, prefix in _ENTITY_PREFIX.items():
                if f"[{prefix}_" in placeholder:
                    stats[entity_type] = stats.get(entity_type, 0) + 1
                    break
        return {
            "total": len(self._dict_cache),
            "by_type": stats,
            "tenant_id": self.tenant_id,
        }
