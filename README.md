# nixstrav-mng

## Dev (LAN)
Jeśli odpalasz na HTTP w sieci lokalnej, ustaw w środowisku:
```
DEV_INSECURE_COOKIES=true
```
Bez tego cookies sesji są `Secure` i logowanie z HTTP kończy się błędem CSRF.

Zarządzanie i obserwowalność systemu **nixstrav** (RFID perimeter guard) w LAN.  
FastAPI + Jinja (server-rendered), SQLite, bez zewnętrznych assetów.

## Funkcje (MVP)
- Logowanie z rolami (admin / operator / viewer), sesje cookie, rate-limit, CSRF, audit log.
- Rejestr tagów (whitelist) z aliasami, grupą (male_tree/female_fruit), pokojem, notatkami, statusem; synchronizacja z `known_tags.json` zapisywana atomowo.
- Dodawanie tagu z czytnika (UI „Dodaj”):
  - Tryb A: **keyboard‑wedge** (domyślny, bez instalacji).
  - Tryb B: lokalny bridge (awaryjnie, browser -> localhost).
  - Tryb C: Web Serial / WebUSB (eksperymentalny, tylko wybrane przeglądarki).
- Podgląd zdarzeń z `events.db` (paginacja, filtry, eksport CSV/JSON).
- Dashboard + heurystyka stanu czytników (last_event per reader, błędy).
- Prosty heartbeat endpoint `/api/v1/system/heartbeat` pod V1 health-model.

## Struktura
```
app/
  main.py               # FastAPI entrypoint
  config.py             # ustawienia z ENV
  database.py, models.py
  routers/              # API + HTML widoki
  services/             # aliasy, known_tags, events, cf601, audit
  templates/, static/   # UI (Jinja + CSS)
systemd/nixstrav-mng.service
tests/
requirements.txt
```

## Wymagania
- Python 3.12 (kod działa także na 3.9+), SQLite.
- Systemd na docelowym serwerze.
- Brak połączenia z internetem w runtime (wszystkie assety lokalnie).

## Konfiguracja przez ENV
- `MNG_DB` – ścieżka do bazy zarządzającej (domyślnie `data/mng.db`).
- `NIXSTRAV_EVENTS_DB` – ścieżka do `events.db` centralnego serwera.
- `NIXSTRAV_KNOWN_TAGS_JSON` – ścieżka do whitelisty `known_tags.json`.
- `NIXSTRAV_CONFIG_JSON` – ścieżka do `config.json` (UI do edycji w V1).
- `SESSION_SECRET` – losowy sekret do podpisywania sesji.
- `CF601_MODE` – `keyboard`, `service` lub `webserial`.
- `CF601D_URL` – baza URL do lokalnej usługi cf601d (np. `http://127.0.0.1:8888`).
- `READER_WARN_SEC`, `READER_OFFLINE_SEC` – progi heurystyki readerow (sekundy).

Opcje bezpieczeństwa (podklucz `SECURITY__...`):
- `SECURITY__SESSION_SECURE` (`true`/`false`) – ustawia flagę `Secure` na cookie.
- `SECURITY__LOGIN_RATE_LIMIT_ATTEMPTS`, `SECURITY__LOGIN_RATE_LIMIT_WINDOW_SEC`, `SECURITY__ACCOUNT_LOCK_MINUTES`.
  Uwaga: przy dev na czystym HTTP ustaw `SECURITY__SESSION_SECURE=false`, inaczej przeglądarka odrzuci cookie.

## Uruchomienie (dev)
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DEV_INSECURE_COOKIES=true
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
UI: `http://localhost:8000/` (HTTP w LAN).  
Domyślny admin tworzony przy starcie jeśli DB pusta: `admin/admin` – zmień od razu.

## Pierwszy start na serwerze (marianserwer)
1) Skopiuj repo do `/opt/nixstrav-mng` i utwórz użytkownika systemowego `nixstrav`.  
2) Utwórz plik `/etc/nixstrav-mng.env`:
```
MNG_DB=/opt/nixstrav-mng/mng.db
NIXSTRAV_EVENTS_DB=/opt/nixstrav/rfid-server/events.db
NIXSTRAV_KNOWN_TAGS_JSON=/opt/nixstrav/rfid-server/known_tags.json
NIXSTRAV_CONFIG_JSON=/opt/nixstrav/rfid-server/config.json
SESSION_SECRET=super-losowy-ciag
CF601_MODE=keyboard          # lub service
CF601D_URL=http://127.0.0.1:8888
```
3) Zainstaluj zależności (virtualenv lub systemowo).  
4) Systemd:
```
sudo cp systemd/nixstrav-mng.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nixstrav-mng.service
```
Usługa nasłuchuje na `:8000` – za reverse proxy (Nginx + TLS self-signed) wystaw `https://192.168.67.10/`.

## Synchronizacja whitelisty
- Aplikacja importuje istniejący `known_tags.json` przy pierwszym starcie (jeśli DB pusta).
- Każda zmiana tagu zapisuje DB i generuje nowy `known_tags.json` atomowo (`tmp + rename` + blokada plikowa `.lock`).

## Czytnik (keyboard‑wedge)
- Domyślnie używamy **keyboard‑wedge**: skan działa jak wpisanie tekstu z klawiatury.
- UI „Dodaj” wymaga **3 potwierdzeń w 3s** i **EPC = 24 znaki hex** (zgodne z nixstrav).
- Skan jest akceptowany **po Enter**, a focus jest utrzymywany na polu skanu.

## Tryby awaryjne
- `CF601_MODE=service`: UI pokazuje panel do lokalnego bridge (endpointy: `/ports`, `/open`, `/start`, `/tags`, `/stop`, `/close`).
  Połączenie jest bezpośrednio z przeglądarki do `CF601D_URL` (nie przez serwer).
  Uwaga na mixed‑content przy HTTPS i wymagany CORS.
- `CF601_MODE=webserial`: tylko Chromium i secure context (HTTPS/localhost).

## CLI
```
python -m app.cli init-db --create-default-admin   # inicjalizacja + admin/admin
python -m app.cli create-user --username alice --password 'haslo' --role operator
```

## Testy
```
pytest -q
```

## Reverse proxy (skrót)
- Nginx: terminacja TLS (self-signed/CA lokalne), proxy_pass do `http://127.0.0.1:8000`.
- Ustaw `client_max_body_size 4m`, wyłącz HSTS jeśli środowisko LAN.
- Ogranicz dostęp do LAN (firewall, bind do 192.168.67.10).

## Uwagi operacyjne
- `events.db` otwierany read-only; brak zależności od internetu w runtime.
- Session cookie `HttpOnly` + CSRF na akcjach mutujących.
- Audit log rejestruje logowania oraz CRUD tagów/użytkowników.
- UI nie używa CDN ani zewnętrznych fontów.
