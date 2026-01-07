# ADR 0001 - Enrollment Modes and Client-side USB

Status: Accepted

## Context
- CF601 USB is on the operator PC; server never talks to operator USB.
- Enrollment must work from a browser on any LAN PC.
- WebSerial/WebUSB requires secure context and has limited browser support.
- Some deployments can run a local cf601d service on the operator PC.

## Decision
- Default to Mode A (keyboard-wedge) for enrollment. It always works.
- Support Mode B via browser -> cf601d on localhost; UI warns about CORS/mixed content.
- Support Mode C (WebSerial/WebUSB) only when feature-detected and in secure context.
- Always provide fallback to Mode A.

## Consequences
- TLS is required for Mode C; reverse proxy must be planned.
- No server-side USB assumptions in code or docs.
- Mode B depends on browser networking and local agent config; support is best-effort.
