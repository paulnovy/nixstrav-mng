# PRD - nixstrav-mng (v1.1)

## Produkt
nixstrav-mng to webapka do zarzadzania systemem nixstrav. Dostep tylko w LAN na serwerze marianserwer (192.168.67.10).

## Krytyczne prawdy
- CF601 USB jest po stronie operatora. Serwer nie ma dostepu do USB operatora.
- Enrollment musi dzialac z przegladarki na dowolnym PC w LAN.
- Mode A (keyboard-wedge) jest domyslny i zawsze dziala.
- WebSerial/WebUSB to opcja. Wymagaja HTTPS (secure context) i maja ograniczone wsparcie.
- Dev env na Ubuntu 24.04 ma PEP 668. Uzywamy venv lub kontenerowego venv.
- Testy uruchamiamy z root repo. pytest.ini ogranicza testpaths do tests.

## Enrollment (CF601)
Mode A (domyslny) - keyboard-wedge:
- dziala w kazdej przegladarce
- UI: duzy input, auto-focus, debounce, normalizacja EPC
- flow: skan -> wykryj istniejacy/nowy -> alias -> zapisz

Mode B (opcjonalny) - cf601d na komputerze operatora:
- przegladarka wola http://127.0.0.1:8888 (lub https z cert)
- ryzyka: CORS + mixed content, gdy panel jest na HTTPS
- UI ma ostrzegac

Mode C (opcjonalny) - Web Serial / WebUSB:
- tylko tam, gdzie wspierane
- wymaga HTTPS (secure context)
- fallback zawsze do Mode A

## Dane i spojnosci
- known_tags.json jako eksport/kompatybilnosc z nixstrav
- zapis atomowy: temp -> fsync -> rename
- events.db read-only dla mng

## Security
- LAN only (firewall/ACL)
- auth + role
- audit log dziala zawsze
- WebSerial/WebUSB implikuje TLS (secure context)

## Observability
- dashboard: OK/WARN/OFFLINE per reader z progami konfigurowalnymi
- health endpoints
- eksport zdarzen

## Dev/Release workflow
- branch per feature (feat/*, fix/*)
- PR -> merge do main
- main ma byc deployable
- testy: pytest -q z root repo
- repo zawiera pytest.ini z testpaths = tests
