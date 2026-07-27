from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from database.engine import Base


class BotText(Base):
    """
    Таблица для динамических текстов бота, редактируемых администратором из СУБД/админки.
    """
    __tablename__ = "bot_texts"
    __table_args__ = (UniqueConstraint("key", "language", name="uq_bot_texts_key_lang"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Ключ текста (например, "dedinside_title")
    key: Mapped[str] = mapped_column(String(64), index=True)
    
    # Язык текста ('ru' или 'en')
    language: Mapped[str] = mapped_column(String(10), default="ru")
    
    # Пользовательский текст
    text: Mapped[str] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<BotText key={self.key} lang={self.language}>"
