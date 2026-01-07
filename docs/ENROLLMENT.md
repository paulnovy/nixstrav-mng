# Enrollment (CF601)

## Summary
Default is Mode A (keyboard-wedge). It must always work in any browser. Modes B/C are optional and must fallback to Mode A.

## Mode A - keyboard wedge (default)
- works in every browser
- UI uses large input, autofocus, debounce
- EPC normalization: pick longest hex token, uppercase (see app/services/epc.py)
- flow: scan -> detect existing/new -> alias -> save

## Mode B - cf601d localhost service (optional)
- browser calls CF601D_URL (default http://127.0.0.1:8888) directly from operator PC
- server never proxies USB
- risks: CORS and mixed content when panel is HTTPS and cf601d is HTTP
- UI must warn

## Mode C - WebSerial/WebUSB (optional)
- only supported in some browsers (Chromium)
- requires secure context (HTTPS or localhost)
- feature detect and show fallback

## Troubleshooting
- No scan: ensure input focus, reader set to keyboard-wedge, and EPC is present
- Mode B: check cf601d running, CORS headers allow panel origin, and protocol matches
- Mode C: check secure context and browser support; otherwise fallback to Mode A
