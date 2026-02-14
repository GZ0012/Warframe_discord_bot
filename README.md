# WF Helper Bot (Chinese Version)

A modular Discord bot built for Warframe utilities, focusing on data synchronization, structured database design, and API-driven automation.

> ⚠️ This repository currently contains the Chinese command version.  
> An English-oriented release will be published in a future update.

---

## Overview

WF Helper Bot is designed as a structured, extensible Discord application that integrates:

- External game APIs
- Local structured databases
- Scheduled synchronization jobs
- Modular command architecture

The project emphasizes backend logic, data reliability, and maintainable code organization rather than simple command scripting.

---

## Core Technical Focus

### 1. Python Backend Architecture
- Asynchronous Discord command handling (`discord.py`)
- Modular command registration system
- Background synchronization tasks
- Structured service separation (commands / sync / core logic)

### 2. Database Layer (SQLite)
- Relic state tracking system
- Status flag management (`Available`, `Vaulted`, `Resurgence`, etc.)
- Metadata persistence (daily sync control, news deduplication)
- Idempotent update logic
- Controlled write access for concurrency safety

The database is treated as a persistent state layer rather than a temporary cache.

### 3. Data Synchronization
- Integration with WarframeStat API
- Automated Prime Resurgence detection
- News scanning with keyword-based filtering
- Daily controlled update cycle (UTC-based)
- Deduplication and state validation logic

This ensures that the bot maintains data accuracy without excessive API requests.

### 4. Modular Expansion Design
The project is intentionally structured to allow additional systems to be added without refactoring existing modules.

Current architecture supports:

- Independent feature modules
- Dedicated sync job modules
- Scalable command registration
- Separation between read-only commands and write-based sync processes

Future systems can be added without modifying the core bot entry point.

---

## Example Feature Categories (Partial)

The bot currently supports selected Warframe utility systems, including:

- Open-world cycle tracking
- Relic status lookup
- Prime Resurgence synchronization
- Structured reminder logic

Additional systems are planned and will be integrated progressively.

---

## Project Structure (Simplified)
bot.py
timecheck/
reminder/
relic_check/


Each module contains isolated logic and can be expanded independently.

---

## Setup

1. Clone the repository
2. Create a `.env` file:
DISCORD_TOKEN=your_token_here
3. Run: python bot.py


---

## Design Philosophy

This project is built with the following principles:

- Data correctness over speed
- Controlled state mutation
- Clear module boundaries
- API abstraction
- Expandability without architectural rewrite

It is intended not just as a utility bot, but as a demonstration of backend design, data handling, and structured Python development.

---

## Future Roadmap

The bot will continue to expand with additional systems and optimization improvements.

The English version with full localization support will be released separately.

---

## License

MIT License



