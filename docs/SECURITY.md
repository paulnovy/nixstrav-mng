# Security

## LAN-only
- Service is LAN only; use firewall/ACL to block WAN.
- Reverse proxy can terminate TLS and restrict hosts.

## Auth and roles
- Roles: admin/operator/viewer.
- Default admin created on empty DB (admin/admin) - change immediately.

## Sessions and CSRF
- Session cookie: HttpOnly + SameSite.
- CSRF token for mutating actions.
- For local HTTP dev set SECURITY__SESSION_SECURE=false.

## Audit log
- Must log logins and CRUD on tags/users.

## TLS / secure context
- WebSerial/WebUSB requires HTTPS (secure context).
- Mode B (cf601d) has CORS/mixed-content risks; warn in UI.
