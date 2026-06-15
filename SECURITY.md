# Security Policy – Malicious Payload Prevention

**Last updated**: 2026-06-15

## Reporting a Security Vulnerability
If you find a vulnerability that could allow **unintended code execution** or **bypass safety checks**, **do not open a public issue**.

Use GitHub’s **private security advisory** (Settings → Security → Advisories) to report it.

We will respond within 3 days (higher priority due to offensive nature).

## Built‑in Safeguards
- The BadUSB classifier includes a **`--safe-mode`** flag that prevents actual execution of untrusted scripts.
- **We strongly recommend** running all analysis in a virtual machine or air‑gapped machine.

## Responsible Disclosure
If you discover a malicious payload or a bypass, please disclose it privately. Do not share exploits publicly.
