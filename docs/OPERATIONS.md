# Operations

## Reader Bridge (Windows)
Operatorzy na Windows muszą uruchomić lokalny bridge HTTP, bo USB jest lokalne i przeglądarka nie ma dostępu do urządzenia.

### Instalacja (nietechniczna)
1. Skopiuj folder `tools/reader-bridge` na komputer operatora.
2. Skopiuj `UHFPrimeReader.dll` z SDK do folderu bridge.
3. Uruchom `install.bat`.
4. Uruchom `run.bat`.

Bridge nasłuchuje na `http://127.0.0.1:8888`.

### Diagnostyka
- `http://127.0.0.1:8888/health` → `{ok: true}`
- Jeśli brak portów COM: sterownik USB‑serial nie jest zainstalowany.

### Ustawienia panelu
W `.env` serwera:
```
CF601_MODE=service
CF601D_URL=http://127.0.0.1:8888
```

### Wymagania
- Windows 10/11
- Python 3.10+
- Sterownik USB‑serial do czytnika
