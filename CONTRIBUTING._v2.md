# Contributing to Auto-Flipper-Tools

**Last updated**: 2026-06-15

## Adding a new payload classifier or automation script
1. Fork the repository.
2. Write your code (Python, shell, or Ducky Script).
3. Include **unit tests** to verify the classifier works without executing malicious code.
4. Ensure your script has a `--dry-run` or `--safe` option if it could write keystrokes.
5. Submit a pull request with a clear description.

## Code style
- Python: `black` + `pylint`
- Shell: `shellcheck`

## Ethical obligation
- **No hardcoded malicious payloads** in the repository.
- **No examples** that demonstrate real‑world attacks on common devices (e.g., automated Windows password dumping).
- **All examples** must be clearly marked as **for educational use only**.

## Pull request checklist
- [ ] I have tested the script in a safe environment (VM / isolated machine).
- [ ] The script does **not** automatically execute untrusted code.
- [ ] Documentation includes warnings and safe‑mode instructions.
- [ ] I have read and agree to the ethics statement.
