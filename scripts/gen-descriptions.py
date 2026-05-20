#!/usr/bin/env python3
"""
gen-descriptions.py — generate description.md for every app in Apps/

Run from repo root:
    python3 scripts/gen-descriptions.py

Overwrites existing description.md files. Review the diff before committing.
"""

from pathlib import Path
import yaml

ROOT = Path(__file__).parent.parent
APPS = ROOT / "Apps"

# fmt: off
# Per-app knowledge base.
# Keys: app dir name (== store_app_id).
# Values: dict with:
#   body       — 2-3 sentence description
#   first      — first-steps hint (omit for headless/CLI-only apps)
#   login      — default credentials string (omit if none / set during wizard)
#   data       — what lives in /DATA/PowerLabAppData/<app>/
#   port_note  — override label for port line (default: "First steps")
APPS_INFO: dict[str, dict] = {
    "actualbudget": {
        "body": "ActualBudget is a local-first personal finance manager built around zero-based budgeting. All data stays on your server — no cloud sync, no subscriptions. Works in any modern browser with optional multi-user support.",
        "first": "Open `http://<host>:15006` after install and create your first budget.",
        "data": "SQLite database containing all budgets, transactions, and accounts.",
    },
    "adminer": {
        "body": "Adminer is a single-file database admin UI that connects to MySQL, MariaDB, PostgreSQL, SQLite, MongoDB, and more. Lighter and faster than phpMyAdmin. Designed for developers who need quick browser-based DB access.",
        "first": "Open `http://<host>:8080` and enter your database server address, credentials, and select the database.",
        "data": "Stateless — no persistent data (connects to an external DB you supply).",
    },
    "affine": {
        "body": "AFFiNE is a next-generation knowledge base that combines docs, whiteboards, and databases in one workspace. Supports real-time collaboration, rich markdown, and edgeless canvas mode. A privacy-friendly alternative to Notion.",
        "first": "Open `http://<host>:3010` and create your workspace. First user becomes the admin.",
        "data": "PostgreSQL data, user uploads, and blob storage.",
    },
    "albyhub": {
        "body": "Alby Hub is a self-custodial Lightning Network node and wallet hub. It manages your channels, routing, and budget rules, and exposes a Nostr Wallet Connect interface for apps to request payments. Built on LDK (Lightning Dev Kit).",
        "first": "Open `http://<host>:58000` and follow the wallet-setup wizard to create or restore your node.",
        "data": "Lightning channel state, wallet secrets, and transaction history.",
    },
    "audiobookshelf": {
        "body": "Audiobookshelf is a self-hosted audiobook and podcast server with a polished web UI and mobile apps (iOS/Android). Supports Audible metadata matching, playback tracking, and multiple libraries across users.",
        "first": "Open `http://<host>:13378` and create the first admin account on the welcome screen.",
        "data": "Libraries, metadata cache, user progress, and podcast downloads.",
    },
    "autobrr": {
        "body": "Autobrr is a modern release automation tool that monitors IRC announce channels and RSS feeds, then pushes matching releases to your download client (qBittorrent, Deluge, SABnzbd, etc.). Replaces autodl-irssi without requiring a full IRC client.",
        "first": "Open `http://<host>:7474` and create the admin account on first launch.",
        "data": "SQLite database with filters, indexers, and release history.",
    },
    "bazarr": {
        "body": "Bazarr automatically downloads subtitles for movies and TV shows managed by Radarr and Sonarr. Supports 50+ subtitle providers including OpenSubtitles, Subscene, and embedded OCR. Integrates directly into the *arr media stack.",
        "first": "Open `http://<host>:6767` → Settings → Connect Sonarr/Radarr with their API keys.",
        "data": "SQLite config, subtitle cache, and provider credentials.",
    },
    "bentopdf": {
        "body": "BentoPDF is a browser-based PDF toolkit for everyday operations: merge, split, compress, rotate, and convert. No file upload to external servers — everything runs locally in your browser via WebAssembly.",
        "first": "Open `http://<host>:8080` and drag-and-drop your PDF to start.",
        "data": "Stateless — no files are stored server-side.",
    },
    "bitmagnet": {
        "body": "Bitmagnet is a self-hosted BitTorrent indexer and search engine. It crawls the DHT network, classifies torrents using built-in metadata enrichment (TMDB, TVDB), and exposes a full-text search UI and GraphQL API. Think of it as your private torrent search engine.",
        "first": "Open `http://<host>:3333` after the initial DHT crawl populates data (allow a few minutes).",
        "data": "PostgreSQL database with torrent metadata, classifications, and crawl state.",
    },
    "booklore": {
        "body": "BookLore is a self-hosted e-book library manager with a clean reader UI, series/author grouping, metadata editing, and reading progress tracking. Supports EPUB and PDF formats. Think of it as your personal Goodreads.",
        "first": "Open `http://<host>:6060` and create the first admin account.",
        "data": "SQLite database with book metadata and reading progress; book files in the configured library path.",
    },
    "calibre-web": {
        "body": "Calibre-Web provides a clean browser interface for your Calibre e-book library, including online reading (EPUB), download, metadata editing, and OPDS catalog for e-readers. Requires an existing Calibre library directory.",
        "first": "Open `http://<host>:8083` — default login is `admin` / `admin123`. Change immediately in User Settings.",
        "login": "`admin` / `admin123`",
        "data": "Calibre library path (bind-mounted), reading progress, and user accounts in a SQLite DB.",
    },
    "campfire": {
        "body": "Campfire is a minimalist, real-time group chat app designed for small teams. No accounts, no apps to install — just share a link and start chatting. Rooms are ephemeral unless persistence is enabled.",
        "first": "Open `http://<host>:80`, enter a room name to create or join it.",
        "data": "Optional SQLite persistence for chat history (ephemeral by default).",
    },
    "chatbot-ui": {
        "body": "Chatbot UI (by McKay Wrigley) is an open-source ChatGPT-style interface that connects to OpenAI, Anthropic, and other LLM APIs. Supports conversation history, custom system prompts, and temperature controls. Requires your own API keys.",
        "first": "Open `http://<host>:3000` and enter your OpenAI or Anthropic API key on the settings screen.",
        "data": "Conversation history and settings in a local database.",
    },
    "chatbotui": {
        "body": "Chatbot UI (alternate build, port 3080) is an open-source ChatGPT-style interface supporting multiple LLM providers including OpenAI, Anthropic, and local Ollama models. Includes folder organization and prompt library.",
        "first": "Open `http://<host>:3080` and configure your LLM provider API key in Settings.",
        "data": "Conversation history and prompt templates in a local database.",
    },
    "chatpad-ai": {
        "body": "ChatPad AI is a privacy-focused ChatGPT desktop-style UI that runs entirely in the browser. Conversations are stored locally in IndexedDB — nothing leaves your network. Supports OpenAI-compatible backends including local Ollama.",
        "first": "Open `http://<host>:80` and enter your API key or point to a local Ollama URL in settings.",
        "data": "Stateless server — all conversation data lives in browser localStorage.",
    },
    "chromium": {
        "body": "Chromium runs a full browser instance inside Docker, accessible via a browser-based VNC/WebRTC interface (KasmVNC). Useful for isolated browsing sessions, web automation, or accessing services that require a visual browser.",
        "first": "Open `http://<host>:3000` — the browser desktop loads directly in your browser tab.",
        "data": "Browser profile, bookmarks, and cached sessions.",
    },
    "code-server": {
        "body": "code-server runs VS Code in the browser, giving you a full IDE accessible from any device. Supports extensions, integrated terminal, Git, and the full VS Code feature set. Ideal for remote development or coding from a tablet.",
        "first": "Open `http://<host>:8080` — the password is printed to the container log on first start (or set via `PASSWORD` env var).",
        "data": "VS Code configuration, extensions, and your workspace files.",
    },
    "copyparty": {
        "body": "Copyparty is a self-hosted file server with a polished web UI, resumable uploads, media player, image gallery, and full-text search. Supports WebDAV and optional authentication. Runs entirely in Python with no database.",
        "first": "Open `http://<host>:3923` — anonymous access is enabled by default; add users in the config to restrict.",
        "data": "Uploaded files and optional SQLite index for search.",
    },
    "crafty": {
        "body": "Crafty Controller is a web-based Minecraft server management panel. It lets you create, start, stop, backup, and monitor multiple Minecraft server instances from a browser. Supports Java and Bedrock editions.",
        "first": "Open `http://<host>:8111` — the default admin credentials are printed to the container log on first start.",
        "data": "Server instances, world saves, configurations, and backups.",
    },
    "dcrpulse": {
        "body": "DCRPulse is a monitoring dashboard for the Decred blockchain network. It tracks block explorers, vote status, treasury transactions, and node stats in real time. Intended for Decred stakeholders and node operators.",
        "first": "Open `http://<host>:8735` after the dcrd backend syncs to the chain tip (may take hours on first run).",
        "data": "dcrd blockchain data, wallet state, and dashboard configuration.",
    },
    "deepsea": {
        "body": "DeepSea is a Decred Proof-of-Stake solo staking management tool. It helps you purchase and manage tickets, monitor voting wallets, and track treasury proposals — all from a browser UI backed by dcrwallet.",
        "first": "Open `http://<host>:8000` and connect it to your running dcrwallet instance.",
        "data": "Staking configuration and ticket purchase history.",
    },
    "deluge": {
        "body": "Deluge is a lightweight, feature-rich BitTorrent client with a web UI, plugin system, and support for remote daemons. It runs headlessly as a daemon and exposes a browser interface for managing downloads.",
        "first": "Open `http://<host>:8112` — default password is `deluge`. Change it immediately in Preferences → Interface.",
        "login": "_(no username)_ / `deluge`",
        "data": "Torrent files, downloaded content, and client configuration.",
    },
    "downtify": {
        "body": "Downtify tracks availability and downtime for websites and services over time, storing the history locally. It provides a simple dashboard showing uptime percentages, response times, and incident timelines.",
        "first": "Open `http://<host>:8582` and add your first monitored endpoint.",
        "data": "SQLite database with uptime history and service configuration.",
    },
    "duplicati": {
        "body": "Duplicati is an encrypted backup client with support for cloud storage backends (S3, Backblaze, Google Drive, SFTP, and many more). Scheduled backups with incremental deduplication and AES-256 encryption.",
        "first": "Open `http://<host>:8200` and add your first backup job — choose a source, a destination, and set a passphrase.",
        "data": "Backup job configurations, schedules, and local database index.",
    },
    "element": {
        "body": "Element is the reference Matrix client, offering end-to-end encrypted messaging, voice/video calls, and rich media sharing. This is the web client only — it requires a separate Matrix homeserver (Synapse or Conduit) to register on.",
        "first": "Open `http://<host>:80` and sign in or register on your Matrix homeserver.",
        "data": "Stateless web client — all data lives on your Matrix homeserver.",
    },
    "emby": {
        "body": "Emby is a media server for personal movies, TV, music, and photos. It transcodes on the fly for any device, supports multiple users with per-user libraries, and provides native apps for most platforms.",
        "first": "Open `http://<host>:8096` and complete the setup wizard to create your admin account and add media libraries.",
        "data": "Emby database (metadata, users, play state) and transcoding cache.",
    },
    "emby-nvidia": {
        "body": "Emby with NVIDIA GPU hardware transcoding enabled. Identical to the standard Emby image but configured to use `runtime: nvidia` for H.264/HEVC hardware acceleration — dramatically reduces CPU load for simultaneous streams.",
        "first": "Open `http://<host>:8096`, complete the setup wizard, then enable hardware transcoding in Admin → Transcoding.",
        "data": "Emby database and transcoding cache. Requires NVIDIA Container Toolkit on the host.",
    },
    "embystat": {
        "body": "EmbyStat aggregates statistics from your Emby server into detailed dashboards: library counts, watched vs. unwatched, user activity, duplicate detection, and more. Read-only — it never modifies your Emby library.",
        "first": "Open `http://<host>:6555` and enter your Emby server URL + API key to connect.",
        "data": "Local stats cache (SQLite) synced from your Emby server.",
    },
    "enclosed": {
        "body": "Enclosed lets you send self-destructing, end-to-end encrypted notes via a shareable URL. The server never sees the plaintext — decryption happens in the recipient's browser using a key embedded in the URL fragment.",
        "first": "Open `http://<host>:8787`, write your note, set the expiry, and share the generated link.",
        "data": "Encrypted note ciphertext (server-side) — plaintext is never stored.",
    },
    "file-drop": {
        "body": "File Drop is a minimal, drag-and-drop file sharing server. Upload a file, get a short link, share it. Files can be set to expire automatically. No accounts required.",
        "first": "Open `http://<host>:3232`, drag your file, copy the link.",
        "data": "Uploaded files and metadata.",
    },
    "firefox": {
        "body": "Firefox runs inside Docker and is served via a browser-based VNC/WebRTC interface (KasmVNC). Useful for isolated browsing, testing web apps behind your VPN, or browsing from a device without a full OS.",
        "first": "Open `http://<host>:3000` — the full Firefox UI loads in your browser tab.",
        "data": "Firefox profile including bookmarks, history, and cookies.",
    },
    "fizzy": {
        "body": "Fizzy is a personal drink tracker and hydration log. Record what you drink, track daily goals, and review intake history over time. Lightweight and private — no data leaves your server.",
        "first": "Open `http://<host>:80` and start logging drinks.",
        "data": "SQLite database with drink logs and user goals.",
    },
    "flaresolverr": {
        "body": "FlareSolverr is a proxy server that bypasses Cloudflare's anti-bot protection using a headless browser. Used as a backend by Jackett, Prowlarr, and other indexer tools when the indexer sits behind Cloudflare.",
        "port_note": "API endpoint",
        "first": "FlareSolverr is a backend service — configure Jackett or Prowlarr to use `http://<host>:8191` as the FlareSolverr URL. No browser UI.",
        "data": "Stateless — no persistent data.",
    },
    "freshrss": {
        "body": "FreshRSS is a self-hosted RSS aggregator with a clean UI, multi-user support, fever/Google Reader API compatibility, and mobile apps (Reeder, FeedMe, Fluent Reader). A full-featured replacement for Google Reader.",
        "first": "Open `http://<host>:80` and complete the installation wizard to create your admin account.",
        "data": "PostgreSQL or SQLite database with feeds, articles, and user preferences.",
    },
    "ghost": {
        "body": "Ghost is a professional blogging and newsletter platform with a built-in editor, subscription management, and Stripe payments. Used by independent creators and small publications as a self-hosted Substack alternative.",
        "first": "Open `http://<host>:2368/ghost` to access the admin panel and complete initial setup.",
        "data": "MySQL/SQLite database, uploaded images, and themes.",
    },
    "grafana": {
        "body": "Grafana is the industry-standard open-source observability platform for building dashboards from time-series data (Prometheus, InfluxDB, Loki, etc.). Used for infrastructure monitoring, application metrics, and log exploration.",
        "first": "Open `http://<host>:3003` — default login is `admin` / `admin`. You are prompted to change the password on first login.",
        "login": "`admin` / `admin`",
        "data": "Grafana SQLite database with dashboards, data sources, and user accounts.",
    },
    "heimdall": {
        "body": "Heimdall is a simple, elegant application dashboard for your self-hosted services. Pin your apps as large tiles with icons, optionally show live stats from supported apps (Sonarr, Radarr, etc.), and access everything from one page.",
        "first": "Open `http://<host>:80` and click the `+` button to add your first application tile.",
        "data": "SQLite database with tile configuration and settings.",
    },
    "homarr": {
        "body": "Homarr is a sleek, customizable home server dashboard with drag-and-drop layout, integrations (Sonarr, Radarr, qBittorrent, Plex, etc.), search widgets, and a Docker container overview. A polished alternative to Heimdall.",
        "first": "Open `http://<host>:7575` and customize your board — tiles, widgets, and integrations.",
        "data": "Dashboard configuration, icon cache, and integration credentials.",
    },
    "homebox": {
        "body": "Homebox is a home inventory management system for tracking items, locations, and purchases. Useful for insurance documentation, moving, or simply knowing where things are. Supports custom fields, labels, and QR codes.",
        "first": "Open `http://<host>:7745` and create the first admin account.",
        "data": "SQLite database with items, locations, labels, and attachments.",
    },
    "homehub": {
        "body": "HomeHub is a unified home automation dashboard that aggregates smart home device states from multiple backends. Displays temperature, lights, locks, and sensors in a single, mobile-friendly view.",
        "first": "Open `http://<host>:5000` and configure your smart home backends.",
        "data": "Configuration files and local state cache.",
    },
    "hortusfox": {
        "body": "HortusFox is a self-hosted plant management app for tracking your plant collection — watering schedules, fertilizing logs, repotting history, and plant health notes. For green-fingered homelab owners.",
        "first": "Open `http://<host>:80` and create your account.",
        "data": "SQLite database with plant records and care history.",
    },
    "hugo": {
        "body": "Hugo is the world's fastest static site generator. This instance runs the Hugo development server, which renders your content in real time and serves it locally. Typically used for previewing before deploying to a CDN.",
        "first": "Open `http://<host>:1313` to see the live preview. Mount your Hugo site content into `/src`.",
        "data": "Your Hugo site source files (bind-mounted).",
    },
    "influxdb2": {
        "body": "InfluxDB 2 is a purpose-built time-series database for metrics, events, and IoT data. It includes a built-in web UI (Chronograf), Flux query language, and a dashboard builder. Commonly paired with Telegraf and Grafana.",
        "first": "Open `http://<host>:8086` and complete the onboarding wizard to create your org, bucket, and admin credentials.",
        "data": "Time-series data, dashboards, and user configuration.",
    },
    "invio": {
        "body": "Invio is a self-hosted invoice and expense tracking tool for freelancers and small businesses. Create professional invoices, track payments, and manage clients — without sending data to a SaaS provider.",
        "first": "Open `http://<host>:8000` and register your account.",
        "data": "SQLite database with invoices, clients, and payment records.",
    },
    "ittools": {
        "body": "IT Tools is a collection of handy utilities for developers and sysadmins: JWT decoder, hash generators, base64 encoder, UUID generator, regex tester, IP calculator, and dozens more. Runs entirely in the browser — no server-side processing.",
        "first": "Open `http://<host>:80` and pick a tool from the sidebar.",
        "data": "Stateless — no data is stored.",
    },
    "jackett": {
        "body": "Jackett is a proxy server that translates the Torznab/Newznab API used by Sonarr/Radarr into searches on hundreds of private and public torrent sites. It handles login cookies, CAPTCHA solving (via FlareSolverr), and result normalization.",
        "first": "Open `http://<host>:9117` and add your torrent indexers. Copy the Torznab feed URL into Sonarr/Radarr.",
        "data": "Indexer configuration, cookies, and API keys.",
    },
    "jellyfin": {
        "body": "Jellyfin is the free, open-source media server for movies, TV, music, and photos — no Premium tier, no tracking. Supports hardware transcoding, live TV/DVR, multiple users, and clients on every platform.",
        "first": "Open `http://<host>:8097` and complete the setup wizard to create your admin account and add media libraries.",
        "data": "Jellyfin metadata database, user data, and transcoding cache.",
    },
    "jellyfin-nvidia": {
        "body": "Jellyfin with NVIDIA GPU hardware transcoding. Identical to the standard Jellyfin image but configured with `runtime: nvidia` for H.264/HEVC/AV1 hardware acceleration, reducing CPU load for concurrent streams.",
        "first": "Open `http://<host>:8097`, complete the setup wizard, then enable hardware transcoding under Admin → Playback.",
        "data": "Jellyfin database and transcoding cache. Requires NVIDIA Container Toolkit on the host.",
    },
    "jotty": {
        "body": "Jotty is a minimal, distraction-free note-taking app. No folders, no tags — just a running list of plain-text notes with instant search. Designed for quick captures that don't belong in a complex knowledge base.",
        "first": "Open `http://<host>:3000` and start writing.",
        "data": "SQLite database with notes.",
    },
    "jupyterlab": {
        "body": "JupyterLab is the next-generation web interface for Jupyter notebooks. Supports Python, R, Julia, and more. Includes a file browser, terminal, text editor, and the classic notebook interface alongside the modern panel layout.",
        "first": "Open `http://<host>:8888` — the access token is printed to the container log on first start.",
        "data": "Notebooks, datasets, and installed Python packages.",
    },
    "kan": {
        "body": "Kan is a self-hosted Kanban board for personal or team task management. Features drag-and-drop cards, labels, due dates, and multiple boards per workspace. A lightweight alternative to Trello or Planka.",
        "first": "Open `http://<host>:3000` and create your workspace.",
        "data": "PostgreSQL database with boards, cards, and user data.",
    },
    "kiwix": {
        "body": "Kiwix serves offline Wikipedia, Stack Overflow, Project Gutenberg, and other web content as ZIM archives — no internet connection required. Ideal for air-gapped environments, schools, or bandwidth-constrained deployments.",
        "first": "Open `http://<host>:8080` and download ZIM content files via the built-in library browser.",
        "data": "ZIM archive files (Wikipedia, etc.) and library index.",
    },
    "kokoro": {
        "body": "Kokoro is a local text-to-speech server powered by the Kokoro TTS model. It exposes an OpenAI-compatible `/v1/audio/speech` API, making it a drop-in offline replacement for cloud TTS in apps that support OpenAI's audio endpoint.",
        "port_note": "API endpoint",
        "first": "Kokoro is a backend service. Point any OpenAI TTS-compatible client at `http://<host>:8880`. No browser UI.",
        "data": "TTS model weights and generation cache.",
    },
    "lazylibrarian": {
        "body": "LazyLibrarian is a book, magazine, and audiobook manager that monitors your reading wishlist and automatically downloads new releases via Usenet or BitTorrent. Integrates with Calibre and Readarr.",
        "first": "Open `http://<host>:5299` and configure your download clients and metadata providers.",
        "data": "SQLite database with book metadata, download history, and library links.",
    },
    "libreoffice": {
        "body": "LibreOffice runs as a containerized desktop environment accessible via VNC/WebRTC. Provides Writer, Calc, Impress, and Draw in a browser tab — useful for editing documents on a server without a local office suite.",
        "first": "Open `http://<host>:3000` — the LibreOffice desktop loads in your browser.",
        "data": "User documents and LibreOffice profile.",
    },
    "lidarr": {
        "body": "Lidarr is an automated music collection manager. It monitors release dates for your followed artists, requests downloads from your configured indexers, and organizes files using MusicBrainz metadata.",
        "first": "Open `http://<host>:8686` → Settings → Media Management to configure your music root folder, then add indexers and download clients.",
        "data": "SQLite database with artist/album metadata, download history, and library index.",
    },
    "linkwarden": {
        "body": "Linkwarden is a collaborative bookmark manager that snapshots pages as PDFs and screenshots so links never die. Supports collections, tags, and multi-user access with per-collection sharing.",
        "first": "Open `http://<host>:3428` and register the first user (becomes admin).",
        "data": "PostgreSQL database, saved page snapshots, and screenshots.",
    },
    "lubelogger": {
        "body": "LubeLogger is a vehicle maintenance and fuel log tracker. Record oil changes, tire rotations, fuel fill-ups, and repairs — complete with cost tracking and service reminders. Supports multiple vehicles.",
        "first": "Open `http://<host>:8080` and add your first vehicle.",
        "data": "SQLite database with vehicle records, maintenance logs, and fuel history.",
    },
    "mailarchiver": {
        "body": "MailArchiver connects to your IMAP mailbox and archives emails to a local searchable database. Full-text search, attachment extraction, and timeline views — your email history stays under your control.",
        "first": "Open `http://<host>:5000` and add your IMAP account credentials to start the initial sync.",
        "data": "PostgreSQL database with archived emails and extracted attachments.",
    },
    "mainsail": {
        "body": "Mainsail is the most popular web interface for Klipper-based 3D printers. It provides real-time print monitoring, temperature graphs, GCode console, webcam support, and configuration file editing from any browser.",
        "first": "Open `http://<host>:80` and configure the Moonraker API URL pointing to your Klipper instance.",
        "data": "Mainsail configuration and cached print data (stateless against Klipper).",
    },
    "mariadb": {
        "body": "MariaDB is a community-developed MySQL-compatible relational database. This instance runs as a headless backend for other apps. Connect with any MySQL-compatible client on port 3306.",
        "port_note": "Database port",
        "first": "MariaDB is a backend service — connect with `mysql -h <host> -P 3306 -u root -p`. Root password is set via the `MYSQL_ROOT_PASSWORD` environment variable.",
        "data": "Database files, binlogs, and InnoDB tablespace.",
    },
    "mazanoke": {
        "body": "Mazanoke is a browser-based image optimizer. It compresses JPEG, PNG, WebP, and AVIF images using efficient algorithms directly in the browser — no server upload required. Useful for optimizing assets before publishing.",
        "first": "Open `http://<host>:80` and drop your images to compress them.",
        "data": "Stateless — no images are stored.",
    },
    "mealie": {
        "body": "Mealie is a self-hosted recipe manager and meal planner with import from any website URL, shopping list generation, nutritional information, and a clean cooking mode. Supports multiple households.",
        "first": "Open `http://<host>:9000` — default login is `changeme@email.com` / `MyPassword`. Change both in User Settings immediately.",
        "login": "`changeme@email.com` / `MyPassword`",
        "data": "PostgreSQL database with recipes, meal plans, and user accounts.",
    },
    "memos": {
        "body": "Memos is a lightweight, Twitter-style note-taking app for short thoughts, quick captures, and daily journals. Notes are displayed in a chronological stream. Supports Markdown, tags, and public/private visibility per memo.",
        "first": "Open `http://<host>:5230` and register the first user (becomes admin).",
        "data": "SQLite database with memos and user accounts.",
    },
    "meshchatx": {
        "body": "MeshChatX is a decentralized group chat app designed for mesh networks and offline/local-area scenarios. Nodes discover each other via mDNS and relay messages peer-to-peer without a central server.",
        "first": "Open `http://<host>:8000`, enter a display name, and join a room — other nodes on the same network auto-discover.",
        "data": "In-memory message history (no persistence by default).",
    },
    "metube": {
        "body": "MeTube is a self-hosted yt-dlp web UI for downloading videos and audio from YouTube, Vimeo, and 1000+ other sites. Supports playlists, format selection, subtitle download, and a download queue.",
        "first": "Open `http://<host>:8081`, paste a URL, choose your format, and hit Download.",
        "data": "Downloaded media files and yt-dlp cookies.",
    },
    "minio": {
        "body": "MinIO is a high-performance, S3-compatible object storage server. Runs on commodity hardware and exposes the full AWS S3 API, making it a drop-in backend for any S3-compatible app. Includes a web console for bucket management.",
        "first": "Open `http://<host>:9010` (web console) — default credentials are `minioadmin` / `minioadmin`. Change immediately in the Identity → Users section.",
        "login": "`minioadmin` / `minioadmin`",
        "data": "Object data, bucket metadata, and IAM configuration.",
    },
    "monetr": {
        "body": "Monetr is a budgeting and personal finance tool focused on forward-looking cash flow — it shows when upcoming bills will hit your account and whether your balance can cover them. Connects to bank accounts via Plaid.",
        "first": "Open `http://<host>:4000` and create your account. Connect a bank account via Plaid or enter transactions manually.",
        "data": "PostgreSQL database with account data, transactions, and budget rules.",
    },
    "mongo": {
        "body": "MongoDB is a document-oriented NoSQL database server. This instance is a headless backend for other apps. Connect on port 27017 with any MongoDB-compatible driver or tool (mongosh, Compass, etc.).",
        "port_note": "Database port",
        "first": "MongoDB is a backend service — connect with `mongosh --host <host> --port 27017`. Credentials are set via `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD` environment variables.",
        "data": "BSON data files, journals, and indexes.",
    },
    "mongodb4": {
        "body": "MongoDB 4 (legacy version) is a document-oriented NoSQL database server pinned to the 4.x release series. Use when an app explicitly requires MongoDB 4 for compatibility. Connect on port 27017.",
        "port_note": "Database port",
        "first": "MongoDB is a backend service — connect with `mongosh --host <host> --port 27017`. Credentials are set via `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD` environment variables.",
        "data": "BSON data files, journals, and indexes.",
    },
    "morphos": {
        "body": "Morphos is a self-hosted file format converter supporting documents, images, audio, and video. Upload a file, pick the output format, download the result. Powered by LibreOffice and FFmpeg under the hood.",
        "first": "Open `http://<host>:8080`, upload a file, and select the target format.",
        "data": "Temporary conversion workspace (files are not permanently stored).",
    },
    "mqttx-web": {
        "body": "MQTTX Web is a browser-based MQTT client for testing and debugging IoT message brokers. Supports MQTT 3.1/3.1.1/5.0, WebSocket transport, JSON payload formatting, and multiple simultaneous connections.",
        "first": "Open `http://<host>:80` and add a connection pointing to your MQTT broker.",
        "data": "Stateless — connection profiles are stored in browser localStorage.",
    },
    "mstream": {
        "body": "mStream is a personal music streaming server with a clean web player, mobile apps, and Subsonic API support. Stream your local music library to any device. Supports playlists, scrobbling, and folder-based browsing.",
        "first": "Open `http://<host>:3000` — default login is `admin` / `admin`. Change immediately in the admin panel.",
        "login": "`admin` / `admin`",
        "data": "Music library (bind-mounted), playlists, and user database.",
    },
    "mylar3": {
        "body": "Mylar3 is an automated comic book downloader and manager. It monitors ComicVine for new issues of your followed series and requests downloads via NZB or torrent. Organizes your CBR/CBZ library automatically.",
        "first": "Open `http://<host>:8090` → Settings → Add your ComicVine API key and configure download clients.",
        "data": "SQLite database with comic metadata, download history, and library index.",
    },
    "n8n": {
        "body": "n8n is a self-hostable workflow automation platform with 400+ integrations (Slack, GitHub, databases, HTTP, AI, etc.). Build complex automation flows with a visual node editor — similar to Zapier but with full code access and no per-action pricing.",
        "first": "Open `http://<host>:5678` and create your owner account on first launch.",
        "data": "SQLite database with workflows, credentials, and execution history.",
    },
    "navidrome": {
        "body": "Navidrome is a fast, lightweight music streaming server compatible with Subsonic and Airsonic clients (DSub, Symfonium, Sonixd, etc.). Scans your music library, reads tags, and serves album art with a built-in web player.",
        "first": "Open `http://<host>:4533` — default login is `admin` / `admin`. Change in User Settings.",
        "login": "`admin` / `admin`",
        "data": "Music library (bind-mounted), SQLite database with scan cache and user data.",
    },
    "neko": {
        "body": "Neko runs a full browser desktop (Firefox, Chromium, etc.) inside Docker and serves it via WebRTC — enabling low-latency, synchronized viewing for multiple users. Perfect for watch parties or shared browsing sessions.",
        "first": "Open `http://<host>:8080` — enter the room password to join (set via `NEKO_PASSWORD` env var).",
        "data": "Browser profile and session state.",
    },
    "networkingtoolbox": {
        "body": "Networking Toolbox is a browser-based collection of network diagnostics: ping, traceroute, DNS lookup, port scanner, Whois, SSL certificate inspector, and more. Runs server-side so it tests from your server's network perspective.",
        "first": "Open `http://<host>:3000` and pick a tool.",
        "data": "Stateless — no persistent data.",
    },
    "nocodb": {
        "body": "NocoDB turns any database (MySQL, PostgreSQL, SQLite, MSSQL) into a smart spreadsheet. It provides a no-code table UI, forms, views, API generation, and role-based access — a self-hosted Airtable alternative.",
        "first": "Open `http://<host>:8080` and create the first superadmin account on the sign-up screen.",
        "data": "NocoDB metadata database and attached file uploads.",
    },
    "nostrudel": {
        "body": "Nostr.club is a feature-rich Nostr client running in the browser. Supports notes, reactions, zaps (Lightning payments), DMs, long-form content, and relay management. Connects directly to your chosen Nostr relays.",
        "first": "Open `http://<host>:80` and log in with your Nostr private key (nsec) or a browser extension (Alby, nos2x).",
        "data": "Stateless — all data is fetched from Nostr relays.",
    },
    "nutstash-wallet": {
        "body": "Nutstash is a self-hosted Cashu e-cash wallet UI. Cashu is an e-cash protocol built on Lightning — tokens are bearer instruments issued by a mint. Nutstash lets you receive, send, and swap e-cash across mints.",
        "first": "Open `http://<host>:3000` and add a Cashu mint URL to start receiving tokens.",
        "data": "E-cash token storage (browser localStorage; no server-side wallet state).",
    },
    "nzbget": {
        "body": "NZBGet is a high-performance Usenet downloader written in C++. It's faster and more CPU-efficient than SABnzbd, with a clean web UI, scripting support, and direct integration with Sonarr/Radarr.",
        "first": "Open `http://<host>:6789` — default login is `nzbget` / `tegbzn6789`. Change in Settings → Security immediately.",
        "login": "`nzbget` / `tegbzn6789`",
        "data": "Downloaded NZB content and client configuration.",
    },
    "obsidian": {
        "body": "Obsidian LiveSync Server provides a self-hosted sync backend for the Obsidian markdown note-taking app. It uses CouchDB under the hood to replicate your vault across all your devices without touching a third-party cloud.",
        "first": "Open `http://<host>:15323` (CouchDB Fauxton UI) to verify the server is up. Then configure Obsidian LiveSync plugin to point at `http://<host>:15323` with your credentials.",
        "data": "CouchDB database with your Obsidian vault replicas.",
    },
    "ollama-amd": {
        "body": "Ollama is a local LLM inference server for running Llama 3, Mistral, Gemma, Phi-3, and other open models. This variant uses ROCm for AMD GPU acceleration (`/dev/kfd`). Exposes an OpenAI-compatible REST API.",
        "port_note": "API endpoint",
        "first": "Ollama is a backend service. Pull a model via CLI: `docker exec <container> ollama pull llama3`. Then point an LLM UI (Open WebUI, Chatbot UI) at `http://<host>:11434`. Requires an AMD GPU with ROCm support.",
        "data": "Downloaded model weights (can be large — tens of GB per model).",
    },
    "ollama-cpu": {
        "body": "Ollama is a local LLM inference server for running Llama 3, Mistral, Gemma, Phi-3, and other open models. This variant uses CPU-only inference — slower, but works on any machine. Exposes an OpenAI-compatible REST API.",
        "port_note": "API endpoint",
        "first": "Ollama is a backend service. Pull a model: `docker exec <container> ollama pull llama3`. Then point an LLM UI at `http://<host>:11434`.",
        "data": "Downloaded model weights (can be tens of GB per model).",
    },
    "ollama-nvidia": {
        "body": "Ollama is a local LLM inference server for running Llama 3, Mistral, Gemma, Phi-3, and other open models. This variant uses CUDA for NVIDIA GPU acceleration. Exposes an OpenAI-compatible REST API.",
        "port_note": "API endpoint",
        "first": "Ollama is a backend service. Pull a model: `docker exec <container> ollama pull llama3`. Then point an LLM UI at `http://<host>:11434`. Requires NVIDIA Container Toolkit on the host.",
        "data": "Downloaded model weights (can be tens of GB per model).",
    },
    "ombi": {
        "body": "Ombi is a media request and user management system for Plex, Emby, and Jellyfin. Users can request movies and TV shows; Ombi pushes approved requests to Radarr/Sonarr automatically.",
        "first": "Open `http://<host>:3579` and complete the setup wizard to connect your media server and *arr instances.",
        "data": "SQLite database with request history, user accounts, and notification settings.",
    },
    "opencode": {
        "body": "OpenCode is a terminal-based AI coding assistant with a web UI. It integrates with LLM providers (OpenAI, Anthropic, local Ollama) to provide code generation, review, and refactoring through a browser interface.",
        "first": "Open `http://<host>:4096` and configure your LLM provider API key.",
        "data": "Session history and configuration.",
    },
    "overseerr": {
        "body": "Overseerr is a modern media request platform for Plex users. It provides a polished interface for browsing TMDB content, requesting downloads, and managing approvals — with Radarr/Sonarr integration and mobile-friendly design.",
        "first": "Open `http://<host>:5055` and complete the setup wizard to sign in with your Plex account and connect *arr instances.",
        "data": "SQLite database with requests, user accounts, and notification settings.",
    },
    "papra": {
        "body": "Papra is a document management system for digitizing and organizing paper documents. Upload scans, extract text via OCR, add tags, and find anything with full-text search. A self-hosted alternative to Paperless-ngx.",
        "first": "Open `http://<host>:1221` and create your account.",
        "data": "Document files, OCR text index, and metadata database.",
    },
    "petio": {
        "body": "Petio is a media request and management app similar to Overseerr, but compatible with both Plex and Emby. Features a Netflix-style discovery UI, automated approval rules, and user notification support.",
        "first": "Open `http://<host>:7777` and complete the setup wizard.",
        "data": "MongoDB database with requests, settings, and user data.",
    },
    "photoprism": {
        "body": "PhotoPrism is an AI-powered photo management server with automatic classification, face recognition, EXIF parsing, map view, and a Google Photos-like UI. Works with your existing folder structure and supports RAW formats.",
        "first": "Open `http://<host>:2342` — default login is `admin` / `insecure`. Change the password immediately via the avatar menu.",
        "login": "`admin` / `insecure`",
        "data": "Photo originals, sidecar metadata, cache thumbnails, and SQLite/MariaDB index.",
    },
    "picsur": {
        "body": "Picsur is a self-hosted image hosting platform — an Imgur alternative. Upload images, get shareable links, and convert between formats on-the-fly. Supports user accounts and API access.",
        "first": "Open `http://<host>:8286` — the default admin password is printed to the container log on first start.",
        "data": "PostgreSQL database with image metadata; image files on disk.",
    },
    "pocketbase": {
        "body": "PocketBase is an open-source backend-as-a-service in a single Go binary. It provides a real-time database (SQLite), built-in auth (email/social), file storage, and an admin UI — ideal for building small apps without writing a backend.",
        "first": "Open `http://<host>:8090/_/` to access the admin UI and create the superadmin account on first launch.",
        "data": "SQLite database with all app data, user records, and file attachments.",
    },
    "postgresql": {
        "body": "PostgreSQL is the world's most advanced open-source relational database. This instance runs as a headless backend for other apps. Connect on port 5432 with any Postgres-compatible client (psql, pgAdmin, etc.).",
        "port_note": "Database port",
        "first": "PostgreSQL is a backend service — connect with `psql -h <host> -p 5432 -U postgres`. Credentials are set via `POSTGRES_PASSWORD` environment variable.",
        "data": "Database cluster data, WAL logs, and PostgreSQL configuration.",
    },
    "poznote": {
        "body": "Poznote is a self-hosted knowledge base and note-taking app with Markdown support, hierarchical organization, and a clean editor. Designed for personal or team documentation without the complexity of a full wiki.",
        "first": "Open `http://<host>:9300` and register your account.",
        "data": "SQLite database with notes and user accounts.",
    },
    "prowlarr": {
        "body": "Prowlarr is the indexer manager for the *arr stack. It centralizes indexer configuration and syncs to Sonarr, Radarr, Lidarr, and Readarr automatically — so you configure each indexer once instead of once per *arr app.",
        "first": "Open `http://<host>:9696` → Settings → Indexers to add sources. Then sync to your *arr apps via Settings → Apps.",
        "data": "SQLite database with indexer configuration and sync state.",
    },
    "pyload": {
        "body": "pyLoad is a download manager for one-click hosters (Mega, RapidGator, etc.), YouTube, and direct links. Features a web UI, plugin system, and unrar/decryption support. The older stable release.",
        "first": "Open `http://<host>:8000` — default login is `admin` / `pyload`. Change in the user settings.",
        "login": "`admin` / `pyload`",
        "data": "Downloaded files and download queue database.",
    },
    "pyload-ng": {
        "body": "pyLoad NG is the actively maintained next-generation rewrite of pyLoad. Download from one-click hosters, YouTube, and direct URLs via a browser UI. Improved plugin API and Python 3 native.",
        "first": "Open `http://<host>:8000` — default login is `admin` / `pyload`. Change in the user settings.",
        "login": "`admin` / `pyload`",
        "data": "Downloaded files and download queue database.",
    },
    "qbittorrent": {
        "body": "qBittorrent is a feature-rich BitTorrent client with a built-in search engine, RSS downloader, sequential downloading, IP filtering, and a clean web UI. The most popular *arr-compatible torrent client.",
        "first": "Open `http://<host>:8181` — default login is `admin` and the temporary password is printed to the container log on first start (qBittorrent 4.6+).",
        "data": "Torrent files, downloaded content, and client settings.",
    },
    "radarr": {
        "body": "Radarr is an automated movie collection manager. It monitors release calendars, grabs downloads from configured indexers when movies become available, and renames/organizes your library using custom naming formats.",
        "first": "Open `http://<host>:7878` → Settings → Media Management to set your movie root folder, then add indexers and download clients.",
        "data": "SQLite database with movie metadata, download history, and library index.",
    },
    "readarr": {
        "body": "Readarr is an automated e-book and audiobook manager, part of the *arr family. It monitors Goodreads for new releases by your followed authors and downloads them via Usenet or torrent.",
        "first": "Open `http://<host>:8787` → Settings → Media Management to set your book root folder, then configure indexers and download clients.",
        "data": "SQLite database with book/author metadata and download history.",
    },
    "readur": {
        "body": "Readur is a self-hosted read-it-later and document archiving service. Save articles, PDFs, and web pages; read them later with full-text search and offline access. A lightweight alternative to Wallabag.",
        "first": "Open `http://<host>:8000` and register your account.",
        "data": "Archived articles, PDFs, and full-text search index.",
    },
    "remmina": {
        "body": "Remmina is a full-featured remote desktop client (RDP, VNC, SSH, SPICE) running inside Docker, accessible via a browser-based UI. Useful for accessing Windows machines or other servers from a browser without installing a local client.",
        "first": "Open `http://<host>:3000` — the Remmina desktop loads in your browser. Add a connection and enter the target host's credentials.",
        "data": "Saved connection profiles and Remmina configuration.",
    },
    "resilio-sync": {
        "body": "Resilio Sync (formerly BitTorrent Sync) uses a peer-to-peer protocol to synchronize folders between devices without a central server. Encrypted in transit, works across LAN and WAN, and supports selective sync.",
        "first": "Open `http://<host>:55555` and add your first sync folder using a secret/link from another Resilio device.",
        "data": "Synchronized folder contents and peer configuration.",
    },
    "sabnzbd": {
        "body": "SABnzbd is a full-featured Usenet downloader with a polished web UI, NZB auto-unpack, repair, and direct integration with Sonarr/Radarr. Python-based and highly configurable.",
        "first": "Open `http://<host>:8282` and complete the quick-start wizard to add a Usenet server and set your download folder.",
        "data": "Downloaded NZB content, incomplete downloads, and client configuration.",
    },
    "sickchill": {
        "body": "SickChill is an automatic TV show downloader that monitors episode air dates and grabs downloads from NZB/torrent indexers. A continuation of SickBeard/SickRage with active maintenance.",
        "first": "Open `http://<host>:8081` → Settings → Search Providers to add indexers and Configure General → Search Settings for your download client.",
        "data": "SQLite database with show metadata, episode history, and settings.",
    },
    "smokeping": {
        "body": "SmokePing continuously measures network latency to a set of targets and generates beautiful round-robin RRD graphs showing latency trends and packet loss over time. Essential for diagnosing intermittent connectivity issues.",
        "first": "Open `http://<host>:10280` to view the latency graphs. Edit `Targets` in the config to add your own hosts.",
        "data": "RRD (round-robin database) files with historical latency measurements.",
    },
    "snapdrop": {
        "body": "Snapdrop enables AirDrop-like file sharing between devices on the same local network — no accounts, no apps, just open the page on both devices and transfer. Works over WebRTC with a WebSocket signaling server.",
        "first": "Open `http://<host>:443` on two devices on the same network — they discover each other automatically. Click a device icon to send files.",
        "data": "Stateless signaling server — files transfer peer-to-peer and are not stored.",
    },
    "sonarr": {
        "body": "Sonarr is an automated TV show collection manager. It monitors episode air dates, grabs downloads from configured indexers when episodes are available, and renames/organizes your library using custom naming templates.",
        "first": "Open `http://<host>:8989` → Settings → Media Management to set your TV root folder, then add indexers and download clients.",
        "data": "SQLite database with show/episode metadata, download history, and library index.",
    },
    "sqlitebrowser": {
        "body": "DB Browser for SQLite (SQLiteBrowser) is a high-quality visual tool for creating, editing, and browsing SQLite databases. This containerized version exposes the full desktop app via a browser-based VNC interface.",
        "first": "Open `http://<host>:3000` — the SQLiteBrowser desktop loads in your browser. Mount your `.db` files as volumes to open them.",
        "data": "SQLite database files you bind-mount into the container.",
    },
    "stirling-pdf": {
        "body": "Stirling-PDF is a self-hosted, all-in-one PDF toolkit with 40+ tools: merge, split, compress, OCR, sign, watermark, convert, and more. Nothing leaves your server — all operations run locally.",
        "first": "Open `http://<host>:8080` and pick a tool from the sidebar.",
        "data": "Temporary processing workspace (output files are returned immediately, not stored).",
    },
    "sure": {
        "body": "Sure is a self-hosted insurance and asset tracking tool. Document your possessions, their values, photos, and warranty information — useful for insurance claims or simply knowing what you own.",
        "first": "Open `http://<host>:23000` and create your account.",
        "data": "PostgreSQL database with asset records and uploaded photos.",
    },
    "swingmusic": {
        "body": "Swing Music is a beautiful self-hosted music player with album art, lyrics, scrobbling (Last.fm), playlist management, and a progressive web app. Browse by artist, album, or genre with instant search.",
        "first": "Open `http://<host>:1970` — it scans your music directory on first start. No login by default (add users in Settings).",
        "data": "SQLite database with library scan cache, playlists, and play history.",
    },
    "syncthing": {
        "body": "Syncthing synchronizes files between your devices continuously, encrypted, and in real time — without a central server or cloud. Devices connect peer-to-peer via relay servers when not on the same LAN.",
        "first": "Open `http://<host>:8384` — the web UI requires no login by default (add a password in Settings → GUI). Add remote devices using their Device ID.",
        "data": "Synced folder contents and Syncthing configuration/database.",
    },
    "tautulli": {
        "body": "Tautulli is the ultimate Plex analytics tool. Track who is watching what, when, and on which device. Generates detailed history reports, notification alerts (stream limits, new content), and playback statistics.",
        "first": "Open `http://<host>:8181` and connect it to your Plex server using a Plex token.",
        "data": "SQLite database with Plex play history, user stats, and notification rules.",
    },
    "termix": {
        "body": "Termix provides a browser-based terminal (xterm.js) connected to a server-side shell. Access a bash/zsh session on your server from any browser — useful when SSH is unavailable or inconvenient.",
        "first": "Open `http://<host>:8080` — a terminal session starts immediately.",
        "data": "Stateless — no persistent shell state.",
    },
    "thinkdashboard": {
        "body": "ThinkDashboard is a personal productivity dashboard combining a todo list, notes, bookmarks, and a Pomodoro timer in a single browser tab. Designed as a browser start page replacement.",
        "first": "Open `http://<host>:8080` and start adding widgets.",
        "data": "SQLite database with todos, notes, and bookmarks.",
    },
    "transmission": {
        "body": "Transmission is a lightweight, fast BitTorrent client with a clean web UI. Lower resource footprint than qBittorrent. Supports remote RPC, watchfolders, blocklists, and encryption.",
        "first": "Open `http://<host>:9091` — default login is `admin` / `admin` (set via `USER`/`PASS` env vars). Change in Settings.",
        "login": "`admin` / `admin` _(configurable via env vars)_",
        "data": "Torrent files, downloaded content, and settings.",
    },
    "trip": {
        "body": "Trip is a self-hosted travel journal and itinerary planner. Log your trips, add photos, map routes, and keep travel notes organized. Private alternative to apps like Polarsteps.",
        "first": "Open `http://<host>:8000` and create your account.",
        "data": "SQLite database with trip records, places, and uploaded photos.",
    },
    "umami": {
        "body": "Umami is a privacy-focused, GDPR-compliant web analytics platform. A self-hosted Google Analytics alternative — no cookies required, no PII collected, simple page-view and event tracking via a lightweight script.",
        "first": "Open `http://<host>:25727` — default login is `admin` / `umami`. Change immediately in Profile settings.",
        "login": "`admin` / `umami`",
        "data": "PostgreSQL database with website events and user accounts.",
    },
    "unifi-controller": {
        "body": "UniFi Network Server (formerly UniFi Controller) is the management software for Ubiquiti UniFi access points, switches, and gateways. Adopt and configure your UniFi hardware from a single dashboard.",
        "first": "Open `http://<host>:8080` — you will be redirected to HTTPS on port 8443. Complete the setup wizard to create your admin account and adopt your UniFi devices.",
        "data": "MongoDB database with device configuration, site topology, and historical stats.",
    },
    "uptime-kuma": {
        "body": "Uptime Kuma is a self-hosted monitoring tool with a beautiful status dashboard. Monitors HTTP, TCP, ping, DNS, and more — with notifications via Telegram, Slack, Discord, email, webhooks, and 90+ other providers.",
        "first": "Open `http://<host>:3001` and create the admin account on the welcome screen.",
        "data": "SQLite database with monitors, status history, and notification config.",
    },
    "uptimekuma": {
        "body": "Uptime Kuma (alternate config) is a self-hosted uptime monitor with a polished status page. Same app as `uptime-kuma` — use this entry if you need a separate instance or different port binding.",
        "first": "Open `http://<host>:3001` and create the admin account on the welcome screen.",
        "data": "SQLite database with monitors, status history, and notification config.",
    },
    "vaultwarden": {
        "body": "Vaultwarden is an unofficial, lightweight Bitwarden server written in Rust. Compatible with all official Bitwarden clients (browser extension, mobile, desktop). Full-featured password manager with vault sharing, TOTP, and attachments.",
        "first": "Open `http://<host>:10380` and register the first user — that account is not automatically an admin. Access the admin panel at `/admin` using the `ADMIN_TOKEN` environment variable.",
        "data": "SQLite database with encrypted vault entries, attachments, and user accounts.",
    },
    "vert": {
        "body": "Vert is a browser-based unit converter covering length, weight, temperature, volume, speed, currency, and more. Runs entirely client-side — no server requests after the initial load.",
        "first": "Open `http://<host>:80` and pick a conversion category.",
        "data": "Stateless — no data stored.",
    },
    "vikunja": {
        "body": "Vikunja is a self-hosted task management app with projects, tasks, subtasks, labels, due dates, Gantt charts, and a Kanban board. Supports teams with per-project sharing and a REST API. A self-hosted Todoist/TickTick.",
        "first": "Open `http://<host>:3456` and register the first user (becomes admin).",
        "data": "PostgreSQL database with tasks, projects, and user data.",
    },
    "wallabag": {
        "body": "Wallabag is a self-hosted read-it-later service. Save articles from any website, strip ads and clutter, and read them offline via the web UI or mobile apps. Supports Pocket/Instapaper import and OPDS export.",
        "first": "Open `http://<host>:25661` — default login is `wallabag` / `wallabag`. Change immediately in User Settings.",
        "login": "`wallabag` / `wallabag`",
        "data": "PostgreSQL database with saved articles, annotations, and tags.",
    },
    "webcheck": {
        "body": "Web Check is an all-in-one OSINT tool for websites: DNS records, WHOIS, SSL certificate details, open ports, security headers, technologies detected, and more — all from a single URL input.",
        "first": "Open `http://<host>:3000`, enter any URL to get a full report.",
        "data": "Stateless — results are fetched in real time, not stored.",
    },
    "wingfit": {
        "body": "WingFit is a self-hosted workout tracking and fitness logging app. Log exercises, sets, reps, and weights. Track progress over time with charts and personal records. No cloud sync required.",
        "first": "Open `http://<host>:8000` and create your account.",
        "data": "SQLite database with workout logs and user profiles.",
    },
    "wizarr": {
        "body": "Wizarr is an invite management system for Jellyfin, Plex, and Emby. Generate invitation links that automatically create accounts on your media server when accepted — complete with onboarding instructions and expiry controls.",
        "first": "Open `http://<host>:5690` and complete the setup wizard to connect your media server and create the first admin account.",
        "data": "SQLite database with invitations, user records, and media server config.",
    },
    "wordpress": {
        "body": "WordPress is the world's most widely used CMS, powering 40%+ of the web. Self-hosting gives you full control over plugins, themes, and data. Requires a MySQL/MariaDB database (not included — install separately or use the WordPress+MariaDB stack).",
        "first": "Open `http://<host>:80` and complete the 5-minute WordPress installation wizard — enter your database credentials and create the admin account.",
        "data": "WordPress uploads, themes, plugins, and MySQL database (external).",
    },
    "yamtrack": {
        "body": "YAMTrack is a self-hosted manga, anime, book, and movie tracker with list management, progress tracking, and AniList/MAL import. A private alternative to MyAnimeList or Anilist.",
        "first": "Open `http://<host>:8000` and register your account.",
        "data": "SQLite database with tracked media and progress.",
    },
    "zen": {
        "body": "Zen is a minimal, distraction-free writing environment for long-form content. Markdown editor with focus mode, word count, and export to HTML/PDF. No accounts — open and write.",
        "first": "Open `http://<host>:8080` and start writing.",
        "data": "Document files stored in the configured data directory.",
    },
    "zeronote": {
        "body": "ZeroNote is a self-hosted, end-to-end encrypted note-taking app. Notes are encrypted client-side before leaving your browser — even the server operator cannot read them. Supports Markdown and notebook organization.",
        "first": "Open `http://<host>:8000` and register your account. Your encryption key is derived from your password.",
        "data": "Encrypted note ciphertext (plaintext never touches the server).",
    },
}
# fmt: on


def render(app_id: str, info: dict, compose_meta: dict) -> str:
    title = compose_meta.get("title", app_id)
    port = compose_meta.get("port")
    port_label = info.get("port_note", "First steps")

    lines = [f"# {title}", "", info["body"]]

    first = info.get("first")
    if first:
        lines += ["", f"**{port_label}:** {first}"]

    login = info.get("login")
    if login:
        lines += ["", f"**Default login:** {login} — change immediately after first login."]

    data = info.get("data")
    if data:
        lines += ["", f"**Data:** `/DATA/PowerLabAppData/{app_id}/` — {data}"]

    lines.append("")
    return "\n".join(lines)


def load_meta(compose_path: Path) -> dict:
    try:
        doc = yaml.safe_load(compose_path.read_text())
    except Exception:
        return {}
    xp = doc.get("x-powerlab") or {}
    pm = xp.get("port_map") or []
    host_port = None
    for e in pm:
        if isinstance(e, dict) and (e.get("protocol", "http").lower() in ("http", "https")):
            host_port = e.get("host")
            break
    return {
        "title": xp.get("title", ""),
        "port": host_port,
    }


def main() -> None:
    if not APPS.is_dir():
        print("ERROR: Apps/ directory not found", flush=True)
        raise SystemExit(1)

    written = skipped = missing = 0
    for app_dir in sorted(APPS.iterdir()):
        if not app_dir.is_dir():
            continue
        app_id = app_dir.name
        if app_id not in APPS_INFO:
            print(f"  WARN: no knowledge entry for {app_id} — skipping")
            missing += 1
            continue
        compose = app_dir / "docker-compose.yml"
        meta = load_meta(compose) if compose.exists() else {}
        content = render(app_id, APPS_INFO[app_id], meta)
        desc = app_dir / "description.md"
        desc.write_text(content)
        written += 1

    print(f"\nDone: {written} written, {skipped} skipped, {missing} missing knowledge entries")


if __name__ == "__main__":
    main()
