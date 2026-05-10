# Security Policy

## Supported Versions

Currently, the FREAK compiler, standard library, and Hangar package manager are under active, rapid development. Security updates are prioritized for the latest stable release and the current active `main` branch.

| Version | Supported |
| ------- | --------- |
| **v0.13.x (Latest)** | :white_check_mark: Yes |
| **main branch** | :white_check_mark: Yes |
| **< v0.13.0** | :x: No |

---

## Reporting a Vulnerability

We take security vulnerabilities in the FREAK compiler, runtime, and package manager seriously. If you discover a vulnerability, please do not disclose it publicly via public GitHub issues.

Instead, please report it privately:

1. **Email:** Send your report directly to **theresa_apocalypse0@proton.me**.
2. **Details:** Include a clear description of the vulnerability, affected components (e.g., runtime memory safety, LLVM code generation, or Hangar package resolution), and a minimal reproducible `.fk` script or test case if possible.

### Response Timeline

* **Acknowledgment:** You should receive acknowledgment of your report within 48 hours.
* **Triage & Patch:** Maintainers will triage the issue, confirm the severity, and prepare a patch privately.
* **Disclosure:** Once a fix is verified and deployed in a new release, a security advisory may be published crediting the reporter (if desired).
