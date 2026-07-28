# Главное меню и кнопки
btn-profile = 👤 Мой профиль
btn-catalog = 📂 Каталог
btn-support = ✍️ Написать Нихао-тян (Поддержка)
btn-admin = ⚙️ Панель управления
btn-cancel = ❌ Отмена
btn-back-to-menu = 🔙 Главное меню
btn-back-to-catalog = 🔙 Назад в каталог
btn-admin-stats = 📊 Статистика
btn-admin-mailing = 📢 Рассылка
btn-admin-users = 👤 Бан/Разбан
btn-admin-texts = 📝 Тексты бота
btn-admin-logs = 📄 Получить логи
btn-admin-tickets = 📬 Обращения ({ $count })
btn-admin-panel = 🔙 Панель управления
admin-tickets-empty = 📭 Все обращения пользователей закрыты или отсутствуют.
admin-tickets-title =
    📬 <b>Обращение #{ $id }</b> [{ $status }]
    
    👤 <b>Отправитель:</b> { $name } (ID: <code>{ $user_id }</code>, @{ $username })
    📅 <b>Дата создания:</b> { $date }
    
    💬 <b>Сообщение:</b>
    <code>{ $message }</code>
btn-ticket-reply = ✉️ Ответить и закрыть
btn-ticket-close-no-reply = ❌ Закрыть без ответа
btn-ticket-prev = ⬅️ Пред.
btn-ticket-next = След. ➡️
admin-ticket-reply-prompt = Введите ваш ответ на обращение #{ $id } (он будет отправлен пользователю, а обращение закроется):
admin-ticket-reply-cancel = Отправка ответа отменена.
admin-ticket-reply-success = ✅ Ответ успешно отправлен, обращение #{ $id } закрыто.
admin-ticket-notification-alert =
    🔔 <b>Новое обращение #{ $id }!</b>
    
    👤 <b>Отправитель:</b> { $name } (@{ $username })
    💬 <b>Сообщение:</b>
    <code>{ $message }</code>
admin-ticket-alert-responded =
    ✅ <b>Обращение #{ $id } закрыто с ответом:</b>
    <code>{ $reply }</code>
user-ticket-closed-simple = 🔔 Ваше обращение #{ $id } было закрыто поддержкой.
user-ticket-closed-with-reply =
    🔔 <b>Ваше обращение #{ $id } закрыто администратором.</b>
    
    💬 <b>Ответ поддержки:</b>
    { $reply }

# Ошибки и ограничения
err-banned-message =
    К сожалению, вы заблокированы в системе Нихао-тян. ❌
    Свяжитесь с администрацией, если это ошибка.
err-banned-callback = Вы заблокированы! Доступ ограничен.
err-no-users = В базе данных нет зарегистрированных пользователей.
err-self-ban = Вы не можете заблокировать самого себя!
err-ban-admin = Вы не можете заблокировать другого администратора!
err-invalid-tg-id = Ошибка! Telegram ID должен состоять только из цифр. Попробуйте еще раз:
err-user-not-found = Пользователь с ID { $id } не найден в базе данных бота.
err-ticket-length =
    Описание тикета должно быть от 10 до 1000 символов.
    Пожалуйста, сформулируйте вопрос корректно.
err-item-not-found = К сожалению, образ не найден.
err-logs-not-found = ❌ Файл логов не найден на сервере.

# Приветствия
welcome-text-start =
    Нихао, { $name }! 🌸
    Я Нихао-тян, твой интерактивный помощник.
    
    Рада видеть тебя! Чем я могу помочь тебе сегодня?
help-text =
    Доступные команды:
    | /start - Запустить бота и войти в меню
    | /help - Показать список команд
    | /about - Информация о Нихао-тян
help-text-admin =
    | /admin - Войти в панель администратора
about-text =
    ✨ <b>Нихао-тян Бот</b> — это высококачественный шаблон Telegram-бота,
    построенный на базе фреймворка Aiogram 3.x и асинхронной СУБД SQLAlchemy 2.0.
    
    Шаблон поддерживает ролевую модель (пользователь/админ), FSM-состояния, защиту от спама (Anti-flood) и полноценную СУБД SQLite/PostgreSQL.
menu-title =
    Главное меню Нихао-тян 🌸
    Выберите интересующий вас раздел:

# Профиль
profile-title =
    👤 <b>Ваш профиль Нихао-тян</b>
    
    ┣ <b>Имя:</b> { $name }
    ┣ <b>Юзернейм:</b> { $username }
    ┣ <b>Telegram ID:</b> <code>{ $id }</code>
    ┣ <b>Роль:</b> <code>{ $role }</code>
    ┣ <b>Активный стиль:</b> { $theme }
    ┗ <b>Дата регистрации:</b> { $date }
profile-username-empty = не установлен
btn-profile-change-theme = 🎨 Сменить стиль

# Поддержка (Тикеты)
support-prompt =
    ✍️ <b>Обращение к Нихао-тян</b>
    
    Опишите вашу проблему или задайте вопрос одним сообщением.
    Мы постараемся ответить как можно быстрее!
support-cancel = Отправка тикета отменена.
support-success =
    ✅ <b>Тикет #{ $id } успешно отправлен!</b>
    
    Нихао-тян получила твое сообщение. Скоро мы свяжемся с тобой!

# Каталог
catalog-title =
    📂 <b>Каталог образов Нихао-тян</b>
    
    Выберите интересующий образ, чтобы узнать подробности:
catalog-item-detail =
    🌸 <b>{ $title }</b>
    
    📝 <b>Описание:</b> { $description }
    
    📊 <b>Популярность:</b> { $rating }

btn-catalog-select = 🌟 Применить стиль
catalog-theme-applied = Стиль "{ $theme }" успешно применен!

# Админ-панель
admin-panel-title =
    ⚙️ <b>Панель управления Нихао-тян</b>
    
    Вы вошли с правами администратора. Выберите действие:
admin-stats-title =
    📊 <b>Статистика бота Нихао-тян</b>
    
    ┣ Всего пользователей в БД: <code>{ $total }</code>
    ┣ Заблокированных пользователей: <code>{ $banned }</code>
    ┗ Открытых тикетов в техподдержку: <code>{ $tickets }</code>
admin-mailing-target-prompt =
    📢 <b>Настройка аудитории рассылки</b>
    
    Выберите, кому именно вы хотите отправить сообщение:
btn-mailing-target-all = 👥 Всем пользователям
btn-mailing-target-filters = 🎨 По фильтрам (Язык/Стиль)
btn-mailing-target-list = 🎯 Выбрать из списка
admin-mailing-filters-prompt =
    🎨 <b>Выбор фильтра рассылки</b>
    
    Выберите критерий таргетинга:
btn-mailing-filter-lang-ru = 🇷🇺 Только RU-локаль
btn-mailing-filter-lang-en = 🇬🇧 Только EN-локаль
btn-mailing-filter-theme = 🎨 По стилям/темам
admin-mailing-themes-prompt =
    🎨 <b>Выбор стиля для рассылки</b>
    
    Выберите образ Нихао-тян, у пользователей которого должна пройти рассылка:
admin-mailing-list-prompt =
    🎯 <b>Выборочная рассылка из списка</b>
    
    Выберите получателей (выбрано: { $count }):
btn-mailing-list-send = ✉️ Написать сообщение ({ $count })
admin-mailing-prompt =
    📣 <b>Отправка контента рассылки</b>
    
    Отправьте сообщение (текст, фото, видео или стикер), которое вы хотите разослать выбранной группе ({ $target }):
admin-mailing-cancel = Рассылка отменена.
admin-mailing-sending = ⏳ Рассылка запущена, пожалуйста, подождите...
admin-mailing-success =
    📊 <b>Рассылка завершена!</b>
    
    ┣ Успешно отправлено: <code>{ $success }</code>
    ┗ Ошибки отправки (блокировка бота): <code>{ $failed }</code>
admin-users-prompt =
    👥 <b>Управление доступом пользователей</b>
    
    Отправьте Telegram ID пользователя, которого вы хотите заблокировать или разблокировать:
admin-users-cancel = Действие отменено.
admin-users-status-changed = Пользователь { $name } (<code>{ $id }</code>) теперь <b>{ $status }</b>.
admin-users-banned = заблокирован ❌
admin-users-unbanned = разблокирован  активен
admin-logs-caption = 📄 Актуальный файл логов бота

# Кнопки выбора языков (для смены языка)
btn-lang-ru = 🇷🇺 Русский
btn-lang-en = 🇬🇧 English
lang-select-prompt = Выберите язык интерфейса / Select your language:
lang-changed = Язык интерфейса успешно изменен! / Interface language has been changed!

# Каталог образов
catalog-classic-title = 🌸 Нихао-тян Классическая
catalog-classic-desc = Стандартная тема Нихао-тян. Любит зеленый чай, вежлива и всегда готова помочь вам с кодом.
catalog-sakura-title = 💮 Нихао-тян Сакура
catalog-sakura-desc = Весенняя нежная тема Нихао-тян. Окружена лепестками сакуры и вдохновляет на создание красивого софта.
catalog-cyberpunk-title = ⚡ Нихао-тян Киберпанк
catalog-cyberpunk-desc = Неоновая хакерская тема Нихао-тян. Пишет скрипты на ассемблере, носит киберимпланты и слушает синтвейв.

# Команда /dedinside
dedinside-title = Здравия желаю господа-коммунисты-бояре!
dedinside-btn-5 = 🔁 Отправить 5 раз
dedinside-btn-10 = 🔁 Отправить 10 раз
dedinside-btn-cancel = ❌ Отмена
dedinside-already-active = ⚠️ Команда /dedinside уже активна! Завершите текущее действие или нажмите Отмена.
dedinside-prompt-text = Напишите сообщение для отправки ({ $count } раз):
dedinside-warn-only-text = ⚠️ Пожалуйста, отправьте именно текстовое сообщение!

# TikTok Модуль
btn-tiktok-account = 📱 Аккаунт TikTok
btn-tiktok-bind = ➕ Привязать аккаунт
btn-tiktok-edit = ✏️ Изменить аккаунт
btn-tiktok-unbind = 🗑️ Отвязать аккаунт
btn-tiktok-unbind-confirm = ✅ Да, отвязать
btn-tiktok-refresh-stats = 🔄 Обновить статистику
tiktok-account-none = не привязан ❌
tiktok-account-title =
    📱 <b>Управление аккаунтом TikTok</b>

    Привязанный аккаунт: <b>{ $username }</b>
tiktok-account-stats-title =
    📱 <b>Профиль TikTok: @{ $username }</b>
    ───────────────────
    👤 <b>Имя:</b> { $nickname }
    👥 <b>Подписчики:</b> { $followers }
    ❤️ <b>Всего лайков:</b> { $likes }
    🎬 <b>Опубликовано видео:</b> { $videos }
    📝 <b>Описание:</b> <i>«{ $bio }»</i>
tiktok-bind-prompt = Отправьте ваш юзернейм TikTok (с символом @ или без него):
tiktok-bind-success = ✅ Аккаунт TikTok <b>@{ $username }</b> успешно привязан!
tiktok-unbind-prompt = Вы уверены, что хотите отвязать аккаунт <b>@{ $username }</b>?
tiktok-unbind-success = 🗑️ Аккаунт TikTok успешно отвязан.

# TikTok Комментарии и Медиа
btn-tiktok-comments = 💬 Комментарии
btn-tiktok-translate = 🌐 Перевести
btn-tiktok-hide-comments = ❌ Скрыть комментарии
tiktok-comment-header = 💬 <b>Комментарий [ { $index } из { $total } ]</b>
tiktok-comment-author = 👤 <b>Автор:</b> { $author }
tiktok-comment-likes = ❤️ <b>Лайков:</b> { $likes }
tiktok-comment-trans-header = 🌐 <b>Перевод на { $lang }:</b>

# TikTok Micro-menus /Mtiktok и /Ptiktok
tiktok-mtiktok-prompt =
    🎵 <b>Скачивание аудио из TikTok</b>

    Отправьте ссылку на видео или фото-пост TikTok:
tiktok-ptiktok-prompt =
    🖼️ <b>Скачивание слайдшоу из TikTok</b>

    Отправьте ссылку на фото-слайдшоу TikTok:
btn-tiktok-download-all = 📥 Скачать все ({ $total })
btn-tiktok-select-slides = 🔢 Выбрать конкретные слайды
btn-tiktok-download-selected = 📥 Скачать выбранное ({ $count })
btn-tiktok-back-mode = 🔙 Назад в выбор режима

