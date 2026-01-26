# UHF Reader Bridge (Windows USB)

Minimalny lokalny bridge HTTP dla czytnika **UHF Desk Reader** pod Windows. Udostępnia EPC przez REST, aby web‑panel mógł czytać tagi z poziomu przeglądarki.

## Wymagania
- Windows 10/11
- Python 3.10+ (zalecane 3.11)
- Sterownik USB‑serial do czytnika (zwykle instaluje się automatycznie lub jest w paczce producenta)
- **UHFPrimeReader.dll** z SDK (skopiować do tego katalogu obok `bridge.py`)

> DLL **nie jest sterownikiem** – to biblioteka SDK, którą ładuje bridge. Sterownik USB‑serial musi być zainstalowany w systemie, żeby pojawił się port COM.

## Instalacja (dla nietechnicznych)
1) Skopiuj cały folder `tools/reader-bridge` na komputer operatora.
2) Skopiuj **UHFPrimeReader.dll** z SDK do tego folderu.
3) Uruchom `install.bat` (dwuklik).

## Uruchomienie
- Kliknij `run.bat` (dwuklik)
- Bridge startuje na `http://127.0.0.1:8888`

## Instalacja (manual)
```powershell
cd tools/reader-bridge
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Skopiuj do katalogu plik:
```
UHFPrimeReader.dll
```

## Uruchomienie (manual)
```powershell
python bridge.py
```
Domyślnie słucha na `http://127.0.0.1:8888`.

## API
- `POST /ports` → `{ ok, ports: ["COM3", ...] }`
- `POST /open` `{ port, baudrate }` → `{ ok, handle }`
- `POST /start` → `{ ok }`
- `POST /tags` → `{ ok, tags: [ { epc, rssi, counts, ant, channel } ] }`
- `POST /stop` → `{ ok }`
- `POST /close` → `{ ok }`
- `GET /health` → `{ ok: true }`

## Notatki
- Bridge działa lokalnie **na komputerze operatora** (USB jest tylko tam).
- Web‑panel (nixstrav‑mng) łączy się do `localhost:8888` po stronie operatora.
