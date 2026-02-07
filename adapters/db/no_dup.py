from typing import Dict, List, Optional, Any
from datetime import datetime
from adapters.db.models import NoDupState


class NoDupRepository:
    """消息去重存储库"""

    @staticmethod
    async def get_link(chat_id: int, link: str) -> Optional[NoDupState]:
        """获取指定群组的链接记录"""
        return await NoDupState.get_or_none(chat_id=chat_id, link=link)

    @staticmethod
    async def get_or_create(
        chat_id: int,
        link: str,
        forwarded_messages: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple[NoDupState, bool]:
        """获取或创建指定群组的链接记录"""
        record, created = await NoDupState.get_or_create(
            chat_id=chat_id,
            link=link,
            defaults={
                "count": 1,
                "forwarded_messages": forwarded_messages or [],
            },
        )
        return record, created

    @staticmethod
    async def increment_count(
        chat_id: int, link: str, forwarded_message: Dict[str, Any]
    ):
        """增加指定群组的计数并添加转发消息记录"""
        record, _ = await NoDupState.get_or_create(
            chat_id=chat_id,
            link=link,
            defaults={
                "count": 1,
                "forwarded_messages": [forwarded_message],
            },
        )

        if not _:  # 记录已存在
            record.count += 1
            if not record.forwarded_messages:
                record.forwarded_messages = []
            record.forwarded_messages.append(forwarded_message)
            await record.save()

        return record

    @staticmethod
    async def get_previous_messages(chat_id: int, link: str) -> List[Dict[str, Any]]:
        """获取指定群组中链接的所有转发消息记录"""
        record = await NoDupState.get_or_none(chat_id=chat_id, link=link)
        if not record:
            return []
        return record.forwarded_messages or []

    @staticmethod
    async def get_count(chat_id: int, link: str) -> int:
        """获取指定群组中链接的转发次数"""
        record = await NoDupState.get_or_none(chat_id=chat_id, link=link)
        return record.count if record else 0

    @staticmethod
    async def delete_link(chat_id: int, link: str) -> bool:
        """删除指定群组的链接记录"""
        deleted_count = await NoDupState.filter(chat_id=chat_id, link=link).delete()
        return deleted_count > 0

    @staticmethod
    async def delete_chat_records(chat_id: int) -> int:
        """删除指定群组的所有记录"""
        deleted_count = await NoDupState.filter(chat_id=chat_id).delete()
        return deleted_count

    @staticmethod
    async def clear_old_records(days: int = 30) -> int:
        """删除超过指定天数的旧记录（全局）"""
        from datetime import timedelta

        threshold_date = datetime.now() - timedelta(days=days)
        deleted_count = await NoDupState.filter(
            last_seen_at__lt=threshold_date
        ).delete()
        return deleted_count

    @staticmethod
    async def get_stats(chat_id: Optional[int] = None) -> Dict[str, Any]:
        """获取去重状态统计信息"""
        if chat_id:
            # 获取指定群组的统计
            records = await NoDupState.filter(chat_id=chat_id).all()
            total_links = len(records)
            total_forwards = sum(record.count for record in records)
            total_messages = sum(
                len(record.forwarded_messages or []) for record in records
            )
            return {
                "chat_id": chat_id,
                "total_tracked_links": total_links,
                "total_forwards": total_forwards,
                "total_messages": total_messages,
            }
        else:
            # 获取全局统计
            all_records = await NoDupState.all()
            total_links = len(all_records)
            total_forwards = sum(record.count for record in all_records)
            total_messages = sum(
                len(record.forwarded_messages or []) for record in all_records
            )

            return {
                "total_tracked_links": total_links,
                "total_forwards": total_forwards,
                "total_messages": total_messages,
            }

    @staticmethod
    async def get_all_records(chat_id: Optional[int] = None) -> List[NoDupState]:
        """获取指定群组的所有记录，或全局所有记录"""
        if chat_id:
            return await NoDupState.filter(chat_id=chat_id).all()
        return await NoDupState.all()
