# Dodawanie tagów (keyboard‑wedge)

## Summary
Domyślny jest Mode A (keyboard‑wedge) i **musi działać zawsze**. Tryby B/C to tylko fallback.

## Mode A — keyboard‑wedge (domyślny)
- działa w każdej przeglądarce
- akceptujemy EPC po **3 potwierdzeniach w 3s**
- EPC musi mieć **24 znaki hex** (96‑bit, zgodne z nixstrav)
- skan przetwarzany **po Enter**
- focus jest utrzymywany na polu skanu
- flow: scan → detect existing/new → alias → save

## Mode B — lokalny bridge (awaryjny)
- browser woła `CF601D_URL` (domyślnie `http://127.0.0.1:8888`) bezpośrednio z PC operatora
- server nigdy nie proxy‑uje USB
- endpointy: `/ports`, `/open`, `/start`, `/tags`, `/stop`, `/close`
- ryzyka: CORS + mixed content gdy panel jest na HTTPS, a bridge na HTTP

## Mode C — WebSerial/WebUSB (awaryjny)
- tylko wybrane przeglądarki (Chromium)
- wymaga secure context (HTTPS lub localhost)

## Troubleshooting
- Brak skanu: sprawdź focus pola, tryb keyboard‑wedge i czytnik wysyła Enter
- Mode B: czy bridge działa, CORS i protokoły zgodne
- Mode C: secure context + wsparcie przeglądarki
