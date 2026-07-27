# Main menu and buttons
btn-profile = 👤 My Profile
btn-catalog = 📂 Catalog
btn-support = ✍️ Write to Nihao-chan (Support)
btn-admin = ⚙️ Admin Panel
btn-cancel = ❌ Cancel
btn-back-to-menu = 🔙 Main Menu
btn-back-to-catalog = 🔙 Back to Catalog
btn-admin-stats = 📊 Statistics
btn-admin-mailing = 📣 Create Broadcast
btn-admin-users = 👥 User Management
btn-admin-panel = 🔙 Control Panel
btn-admin-logs = 📋 Get Logs
btn-admin-tickets = 📬 Tickets ({ $count })
admin-tickets-empty = 📭 All user tickets are closed or empty.
admin-tickets-title =
    📬 <b>Ticket #{ $id }</b> [{ $status }]
    
    👤 <b>Sender:</b> { $name } (ID: <code>{ $user_id }</code>, @{ $username })
    📅 <b>Created At:</b> { $date }
    
    💬 <b>Message:</b>
    <code>{ $message }</code>
btn-ticket-reply = ✉️ Reply and Close
btn-ticket-close-no-reply = ❌ Close without Reply
btn-ticket-prev = ⬅️ Prev
btn-ticket-next = Next ➡️
admin-ticket-reply-prompt = Enter your reply for ticket #{ $id } (it will be sent to the user and the ticket will be closed):
admin-ticket-reply-cancel = Sending reply cancelled.
admin-ticket-reply-success = ✅ Reply sent successfully, ticket #{ $id } is closed.
admin-ticket-notification-alert =
    🔔 <b>New ticket #{ $id }!</b>
    
    👤 <b>Sender:</b> { $name } (@{ $username })
    💬 <b>Message:</b>
    <code>{ $message }</code>
admin-ticket-alert-responded =
    ✅ <b>Ticket #{ $id } closed with reply:</b>
    <code>{ $reply }</code>
user-ticket-closed-simple = 🔔 Your ticket #{ $id } has been closed by support.
user-ticket-closed-with-reply =
    🔔 <b>Your ticket #{ $id } has been closed by support.</b>
    
    💬 <b>Support reply:</b>
    { $reply }

# Errors and limitations
err-banned-message =
    Unfortunately, you are banned in the Nihao-chan system. ❌
    Contact support if this is a mistake.
err-banned-callback = You are banned! Access denied.
err-no-users = There are no registered users in the database.
err-self-ban = You cannot ban yourself!
err-ban-admin = You cannot ban another administrator!
err-invalid-tg-id = Error! Telegram ID must consist of digits only. Try again:
err-user-not-found = User with ID { $id } was not found in the bot's database.
err-ticket-length =
    Support ticket description must be from 10 to 1000 characters.
    Please formulate your question correctly.
err-item-not-found = Unfortunately, this style was not found.
err-logs-not-found = ❌ Log file not found on the server.

# Welcomes
welcome-text-start =
    Nihao, { $name }! 🌸
    I am Nihao-chan, your interactive assistant.
    
    Glad to see you! How can I help you today?
help-text =
    Available commands:
    | /start - Launch the bot and enter menu
    | /help - Show list of commands
    | /about - About Nihao-chan
help-text-admin =
    | /admin - Enter the administrator panel
about-text =
    ✨ <b>Nihao-chan Bot</b> is a high-quality Telegram bot boilerplate,
    built on the Aiogram 3.x framework and SQLAlchemy 2.0 Async database.
    
    The boilerplate supports role model (user/admin), FSM states, anti-flood protection, and SQLite/PostgreSQL database.
menu-title =
    Nihao-chan Main Menu 🌸
    Select the section you are interested in:

# Profile
profile-title =
    👤 <b>Nihao-chan Profile</b>
    
    ┣ <b>Name:</b> { $name }
    ┣ <b>Username:</b> { $username }
    ┣ <b>Telegram ID:</b> <code>{ $id }</code>
    ┣ <b>Role:</b> <code>{ $role }</code>
    ┣ <b>Active Style:</b> { $theme }
    ┗ <b>Registration Date:</b> { $date }
profile-username-empty = not set
btn-profile-change-theme = 🎨 Change Style

# Support (Tickets)
support-prompt =
    ✍️ <b>Contacting Nihao-chan</b>
    
    Describe your issue or ask your question in one message.
    We will try to reply as soon as possible!
support-cancel = Sending ticket cancelled.
support-success =
    ✅ <b>Ticket #{ $id } sent successfully!</b>
    
    Nihao-chan received your message. We will contact you soon!

# Catalog
catalog-title =
    📂 <b>Nihao-chan Styles Catalog</b>
    
    Select the style you want to view details for:
catalog-item-detail =
    🌸 <b>{ $title }</b>
    
    📝 <b>Description:</b> { $description }
    
    📊 <b>Rating:</b> { $rating }

btn-catalog-select = 🌟 Apply Style
catalog-theme-applied = Style "{ $theme }" has been successfully applied!

# Admin Panel
admin-panel-title =
    ⚙️ <b>Nihao-chan Control Panel</b>
    
    Logged in with admin rights. Select an action:
admin-stats-title =
    📊 <b>Nihao-chan Bot Statistics</b>
    
    ┣ Total users in DB: <code>{ $total }</code>
    ┣ Banned users: <code>{ $banned }</code>
    ┗ Open support tickets: <code>{ $tickets }</code>
admin-mailing-target-prompt =
    📢 <b>Broadcast Audience Setup</b>
    
    Select who you want to send the message to:
btn-mailing-target-all = 👥 All Users
btn-mailing-target-filters = 🎨 By Filters (Lang/Style)
btn-mailing-target-list = 🎯 Select from List
admin-mailing-filters-prompt =
    🎨 <b>Select Broadcast Filter</b>
    
    Select targeting criteria:
btn-mailing-filter-lang-ru = 🇷🇺 Only RU-locale Users
btn-mailing-filter-lang-en = 🇬🇧 Only EN-locale Users
btn-mailing-filter-theme = 🎨 By Styles/Themes
admin-mailing-themes-prompt =
    🎨 <b>Select Style for targeting</b>
    
    Select the Nihao-chan style users of which should receive this broadcast:
admin-mailing-list-prompt =
    🎯 <b>Selective Broadcast from List</b>
    
    Select recipients (selected: { $count }):
btn-mailing-list-send = ✉️ Send Message ({ $count })
admin-mailing-prompt =
    📣 <b>Send Broadcast Content</b>
    
    Send the message (text, photo, video, or sticker) you want to broadcast to the selected group ({ $target }):
admin-mailing-cancel = Broadcast cancelled.
admin-mailing-sending = ⏳ Broadcast started, please wait...
admin-mailing-success =
    📊 <b>Broadcast finished!</b>
    
    ┣ Successfully sent: <code>{ $success }</code>
    ┗ Sending errors (bot blocked): <code>{ $failed }</code>
admin-users-prompt =
    👥 <b>User Access Management</b>
    
    Send the Telegram ID of the user you want to ban or unban:
admin-users-cancel = Action cancelled.
admin-users-status-changed = User { $name } (<code>{ $id }</code>) is now <b>{ $status }</b>.
admin-users-banned = banned ❌
admin-users-unbanned = unbanned  active
admin-logs-caption = 📄 Current bot log file

# Language buttons
btn-lang-ru = 🇷🇺 Русский
btn-lang-en = 🇬🇧 English
lang-select-prompt = Выберите язык интерфейса / Select your language:
lang-changed = Язык интерфейса успешно изменен! / Interface language has been changed!

# Catalog Items
catalog-classic-title = 🌸 Nihao-chan Classic
catalog-classic-desc = Standard Nihao-chan theme. Loves green tea, polite and always ready to help you with code.
catalog-sakura-title = 💮 Nihao-chan Sakura
catalog-sakura-desc = Spring gentle Nihao-chan theme. Surrounded by sakura petals and inspires to write beautiful software.
catalog-cyberpunk-title = ⚡ Nihao-chan Cyberpunk
catalog-cyberpunk-desc = Neon hacker Nihao-chan theme. Writes scripts in assembler, wears cyberimplants and listens to synthwave.
