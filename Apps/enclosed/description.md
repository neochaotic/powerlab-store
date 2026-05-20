# Enclosed

Enclosed lets you send self-destructing, end-to-end encrypted notes via a shareable URL. The server never sees the plaintext — decryption happens in the recipient's browser using a key embedded in the URL fragment.

**First steps:** Open `http://<host>:8787`, write your note, set the expiry, and share the generated link.

**Data:** `/DATA/PowerLabAppData/enclosed/` — Encrypted note ciphertext (server-side) — plaintext is never stored.
