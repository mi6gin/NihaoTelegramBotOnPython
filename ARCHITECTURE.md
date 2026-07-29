# Architecture

The project follows a layered architecture with dependencies pointing inward:

```text
Telegram presentation
        |
        v
Application services
        |
        v
Domain

Infrastructure --------> Application ports / Domain
```

## Layers

### `domain/`

Framework-independent business values and rules. It must not import Aiogram,
SQLAlchemy, repositories, HTTP clients, or presentation modules.

Current modules:

- `tiktok.py` normalizes post metadata.
- `mailing.py` describes mailing audiences.
- `support.py` validates support-ticket messages.

### `application/services/`

Use-case orchestration. Services depend on domain objects and small `Protocol`
ports, not on concrete databases or Telegram.

Current services:

- `TikTokService` coordinates post references, metadata, and comment state.
- `MailingService` resolves an audience through a repository port.
- `SupportService` creates a validated ticket and obtains its recipients.

### `infrastructure/` and `database/`

Concrete adapters for external systems.

- `infrastructure/tiktok/` contains the HTTP/`yt-dlp` TikTok adapter.
- `database/models/` contains SQLAlchemy mappings.
- `database/repository/` contains persistence implementations.

`database/` is retained as a top-level package because Alembic migrations and
existing imports rely on it; architecturally it belongs to infrastructure.

### Telegram presentation

`presentation/telegram/` contains all Aiogram routers and handlers, grouped by
audience or feature:

- `user/` contains user-facing routes.
- `admin/` contains administrative routes.
- `tiktok/` contains the TikTok feature routes, states, and keyboards.
- `errors/` contains global error routes.
- `router.py` composes them into the root router.

Shared keyboards, filters, and middleware remain in their top-level packages.
Together these modules translate Aiogram events into application service calls
and render the results.

### `application/`

The package root is also the composition and lifecycle layer. `bootstrap.py`
wires concrete adapters to the bot and owns startup/shutdown.

## Dependency rules

1. `domain` imports only the Python standard library and other domain modules.
2. `application.services` may import `domain`, but not Aiogram, SQLAlchemy,
   presentation, repositories, or infrastructure.
3. Presentation may call application services and format domain results.
4. Infrastructure implements ports required by application services.
5. Repositories own queries and transactions; handlers must not build new
   SQLAlchemy queries.

`tests/test_architecture.py` enforces the first two rules.

## Adding a feature

1. Put invariants and framework-independent values in `domain/`.
2. Define the use case and dependency protocols in `application/services/`.
3. Implement protocols in `database/repository/` or `infrastructure/`.
4. Wire the implementation at the presentation/composition edge.
5. Keep handlers focused on input parsing, service invocation, and output.
