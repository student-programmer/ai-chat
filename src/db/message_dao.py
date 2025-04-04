from datetime import datetime
from typing import List, Tuple, Optional

from .base_dao import BaseDAO
from .constants import DATE_FORMAT

class MessageDAO(BaseDAO):
    """DAO для работы с сообщениями"""
    def _init_db(self):
        self._execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp DATETIME,
                rating INTEGER DEFAULT 0,
                topic_id INTEGER,
                FOREIGN KEY(chat_id) REFERENCES chats(id),
                FOREIGN KEY(topic_id) REFERENCES topics(id)
            )
        ''')

    def get_messages(self, chat_id: int) -> List[Tuple]:
        cursor = self._execute('''
            SELECT m.id, m.role, m.content, m.timestamp, m.rating, m.topic_id 
            FROM messages m
            WHERE chat_id = ? 
            ORDER BY timestamp ASC''',
            (chat_id,))
        return cursor.fetchall()

    def add_message(self, chat_id: int, role: str, content: str) -> int:
        cursor = self._execute(
            '''INSERT INTO messages 
               (chat_id, role, content, timestamp, rating, topic_id)
               VALUES (?, ?, ?, ?, 0, 1)''',
            (chat_id, role, content, datetime.now().strftime(DATE_FORMAT)))
        return cursor.lastrowid

    def update_field(self, message_id: int, field: str, value: str | int) -> None:
        allowed_fields = {'rating', 'topic_id'}
        if field not in allowed_fields:
            raise ValueError(f"Недопустимое поле для обновления: {field}")
        self._execute(
            f'UPDATE messages SET {field} = ? WHERE id = ?',
            (value, message_id))
