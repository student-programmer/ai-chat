from typing import List, Tuple

from .base_dao import BaseDAO
from .constants import DEFAULT_TOPICS


class TopicDAO(BaseDAO):
    """DAO для работы с темами"""
    def _init_db(self):
        self._execute('''
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE
            )
        ''')
        self._init_default_topics()

    def _init_default_topics(self):
        """Инициализация стандартных тем"""
        for topic in DEFAULT_TOPICS:
            self._execute(
                "INSERT OR IGNORE INTO topics (name) VALUES (?)",
                (topic,)
            )

    def get_all_topics(self) -> List[Tuple[int, str]]:
        cursor = self._execute('SELECT id, name FROM topics ORDER BY name')
        return cursor.fetchall()

    def get_topic_name(self, topic_id: int) -> str:
        cursor = self._execute('SELECT name FROM topics WHERE id = ?', (topic_id,))
        return cursor.fetchone()[0]
