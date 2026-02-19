# WF Helper Bot (Chinese Version)

A modular Discord bot built for Warframe utilities, focusing on API-driven automation, structured database design, and real-time market intelligence.

> ⚠️ This repository currently contains the Chinese command version.  
> A fully localized English release will be published in a future update.

---

## Overview

WF Helper Bot is a structured and extensible Discord application designed to provide real-time Warframe utilities through:

- External API integration
- Market data processing
- Persistent database state management
- Scheduled background synchronization
- Event-based reminder systems

The project emphasizes backend system design, reliable data handling, and scalable architecture rather than simple command scripting.

---

## Core Technical Architecture

### 1. Python Backend System

- Asynchronous Discord command handling (`discord.py`)
- Modular command registration
- Background sync task scheduling
- Service-based structure separation:
  - Commands
  - Sync Jobs
  - Core Logic
  - Market Integration
  - Reminder Systems

The architecture allows new systems to be added without modifying the main bot entry point.

---

### 2. Database Layer (SQLite Persistent Storage)

The database is treated as a long-term state layer rather than temporary cache.

Key design aspects:

- Relic state tracking system
- Vault status detection (`Vaulted`, `Available`, `Resurgence`)
- Controlled daily sync flags
- News and update deduplication
- Idempotent update logic
- Concurrency-safe write control
- Reminder subscription persistence

State mutation is carefully controlled to avoid inconsistent data across restarts.

---

### 3. Market Data Integration (Warframe Market API)

The bot integrates with Warframe Market to provide:

- Item price lookup
- Real-time lowest sell order query
- Market search functionality
- Price monitoring logic
- Market-based alert triggers

Planned improvements:

- Historical price tracking
- Price volatility detection
- Arbitrage opportunity alerts

---

### 4. Relic Intelligence System

The bot supports structured relic analysis:

- Relic lookup
- Vaulted status detection
- Prime Resurgence state tracking
- Relic drop verification logic

This ensures relic availability information stays synchronized with current game state.

---

### 5. Real-Time Fissure & Event Monitoring

Comprehensive fissure tracking system:

- All fissure type detection
- Real-time fissure lookup
- Fissure reminder subscriptions
- Open-world cycle tracking
- Plains / Orb Vallis / Cambion Drift notifications
- Market reminder alerts

Users can subscribe to specific event conditions and receive automated notifications.

---

## Feature Categories (Expandable)

Current systems include:

- Market price lookup & monitoring
- Relic state tracking & vault detection
- Prime Resurgence synchronization
- Fissure monitoring & reminders
- Open-world cycle tracking
- Structured notification systems

Additional systems are continuously being developed and integrated.

---

## Project Structure (Simplified)

bot.py
core/
sync/
market/
relic/
fissure/
reminder/
timecheck/


Each module is independently expandable without breaking the overall architecture.

---

## Setup

1. Clone the repository
2. Create a `.env` file (adding the token inside)
3. Install dependencies (pip install -r requirements.txt)
4. Run the bot (python bot.py)



---

## Design Philosophy

This project is built around the following principles:

- Data correctness over speed
- Persistent state reliability
- Controlled state mutation
- Clear module boundaries
- API abstraction
- Modular expansion capability
- Backend-first system thinking

It is designed not only as a utility bot, but as a demonstration of:

- Structured Python backend development
- API-driven automation systems
- Market data processing
- Persistent database management
- Scalable Discord bot architecture

---

## Roadmap

Future expansions may include:

- Historical market data analytics
- Advanced price alert customization
- Multi-language command support
- Web dashboard integration
- Performance optimization & caching improvements

---

## License

MIT License

