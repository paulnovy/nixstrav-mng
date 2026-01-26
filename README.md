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
- Enrollment tagu z czytnika CF601:
  - Tryb A: keyboard wedge (pole input).
  - Tryb B: lokalny agent `cf601d` (HTTP kompatybilny z vendorem; browser -> localhost).
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
uvicorn app.main:app --reload --port 8000
```
UI: `https://localhost:8000/` (zalecany TLS nawet w LAN).  
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

## CF601
- Tryb `keyboard`: wejście /enroll -> pole EPC z fokusem, skan z klawiatury.
- Tryb `service`: panel w /enroll z przyciskami do usług `cf601d` (`/getPorts`, `/OpenDevice`, `/StartCounting`, `/GetTagInfo`, `/InventoryStop`, `/CloseDevice`).
  Połączenie jest bezpośrednio z przeglądarki do `CF601D_URL` (nie przez serwer).
  Uwaga na mixed-content przy HTTPS i wymagany CORS.
- Tryb `webserial`: tylko wybrane przeglądarki (Chromium) i secure context (HTTPS/localhost).

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
