import streamlit as st
import uuid

from datetime import datetime

from typing_extensions import Optional

from db import ChatDAO, MessageDAO, DATE_FORMAT, TopicDAO, RATING_OPTIONS
from typing import Tuple


class ChatInterface:
    """Класс для управления пользовательским интерфейсом чата"""

    def __init__(self):
        self.chat_dao = ChatDAO()
        self.message_dao = MessageDAO()
        self.topic_dao = TopicDAO()
        self._init_session_state()

    @staticmethod
    def _init_session_state():
        """Инициализация состояния сессии"""
        if 'current_chat' not in st.session_state:
            st.session_state.current_chat = None

    def render_sidebar(self):
        """Отрисовка боковой панели с чатами"""
        with st.sidebar:
            st.header("Чаты")
            self._render_new_chat_button()
            self._render_chat_history()

    def _render_new_chat_button(self):
        """Кнопка создания нового чата"""
        if st.button("+ Новый чат"):
            new_chat_id = self.chat_dao.create_chat()
            st.session_state.current_chat = new_chat_id
            st.rerun()

    def _render_chat_history(self):
        """Отображение истории чатов"""
        st.subheader("История чатов")
        chats = self.chat_dao.get_all_chats()

        for chat in chats:
            self._render_chat_button(chat)

    def _render_chat_button(self, chat: tuple):
        """Отрисовка кнопки чата в истории"""
        chat_id, title, created_at = chat
        formatted_date = datetime.strptime(
            created_at, DATE_FORMAT).strftime('%d.%m %H:%M')

        # Форматирование отображаемого названия
        display_title = (title[:15] + '...') if len(title) > 18 else title
        button_label = f"{display_title} ({formatted_date})"
        if st.button(button_label, key=f"chat_{chat_id}", use_container_width=True):
            st.session_state.current_chat = chat_id
            st.rerun()

    def render_main_interface(self):
        """Отрисовка основного интерфейса чата"""
        if not st.session_state.current_chat:
            self._render_empty_state()
            return

        self._render_chat_header()
        messages = self.message_dao.get_messages(st.session_state.current_chat)
        print(messages)
        self._render_messages(messages)
        self._handle_user_input()

    def _render_empty_state(self):
        """Отображение состояния при отсутствии выбранного чата"""
        st.info("Создайте новый чат или выберите существующий из списка слева")

    def _render_chat_header(self):
        """Заголовок чата с возможностью редактирования"""
        col1, col2 = st.columns([0.7, 0.3])
        with col1:
            st.header(self._get_current_chat_title())

    def _get_current_chat_title(self) -> str:
        """Получение текущего названия чата"""
        chats = self.chat_dao.get_all_chats()
        for chat in chats:
            if chat[0] == st.session_state.current_chat:
                return chat[1]
        return "Неизвестный чат"

    def _render_messages(self, messages: list):
        """Отображение всех сообщений чата"""
        for msg in messages:
            self._render_message(msg)

    def _render_message(self, msg: tuple):
        """Отрисовка отдельного сообщения"""
        message_id, role, content, timestamp, rating, topic_id = msg
        topic = self.topic_dao.get_topic_name(topic_id)
        with st.chat_message(role):
            self._render_message_controls(role, message_id, topic, rating)
            st.write(content)
            st.caption(timestamp)

    def _render_message_controls(self, role: str, message_id: int,current_topic: str, current_rating: Optional[int]=None):
        """Управление сообщением: оценка и тема"""
        if role == 'assistant':
            self._render_rating_control(message_id, current_rating)
        else:
            self._render_topic_control(message_id, current_topic)

    def _render_rating_control(self, message_id: int, current_rating: Optional[int]=None):
        """Контрол оценки для сообщений ассистента"""
        print(RATING_OPTIONS)
        print(current_rating)
        if current_rating is None:
            current_rating = len(RATING_OPTIONS)
        new_rating = st.selectbox(
            "Оцените ответ:",
            options=RATING_OPTIONS,
            format_func=lambda x: "★" * x if x > 0 else "Не оценено",
            index=current_rating,
            key=f"rating_{message_id}"
        )
        if new_rating != current_rating:
            self.message_dao.update_field(message_id, 'rating', new_rating)
            st.rerun()

    def _render_topic_control(self, message_id: int, current_topic: str):
        """Контрол выбора темы для сообщения"""
        topics = self.topic_dao.get_all_topics()
        topic_names = [t[1] for t in topics]

        try:
            current_index = topic_names.index(current_topic)
        except ValueError:
            current_index = 0

        new_topic = st.selectbox(
            "**Тема:**",
            options=topic_names,
            index=current_index,
            key=f"topic_{message_id}"
        )

        if new_topic != current_topic:
            topic_id = next(t[0] for t in topics if t[1] == new_topic)
            self.message_dao.update_field(message_id, 'topic_id', topic_id)
            st.rerun()

    def _handle_user_input(self):
        """Обработка пользовательского ввода"""
        if user_input := st.chat_input("Введите сообщение..."):
            self._process_user_input(user_input)

    def _process_user_input(self, user_input: str):
        """Обработка нового сообщения пользователя"""
        # Автогенерация названия чата при первом сообщении
        if self._is_first_message_in_chat():
            self._generate_chat_title(user_input)

        # Сохранение сообщения пользователя
        self.message_dao.add_message(
            st.session_state.current_chat,
            'user',
            user_input
        )

        # Генерация и сохранение ответа бота
        self._generate_bot_response(user_input)
        st.rerun()

    def _is_first_message_in_chat(self) -> bool:
        """Проверка, является ли сообщение первым в чате"""
        messages = self.message_dao.get_messages(st.session_state.current_chat)
        return len(messages) == 0

    def _generate_chat_title(self, first_message: str):
        """Генерация названия чата на основе первого сообщения"""
        auto_title = (first_message[:30] + "...") if len(first_message) > 30 else first_message
        self.chat_dao.update_chat_title(
            st.session_state.current_chat,
            auto_title
        )

    def _generate_bot_response(self, user_input: str):
        """Генерация ответа бота (заглушка)"""
        bot_response = f"Вы сказали: {user_input}"
        self.message_dao.add_message(
            st.session_state.current_chat,
            'assistant',
            bot_response
        )

def main():
    chat_interface = ChatInterface()
    chat_interface.render_sidebar()
    chat_interface.render_main_interface()


if __name__ == "__main__":
    main()