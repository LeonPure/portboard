# Security policy

## Supported versions

PortBoard is currently an alpha project. Security fixes are provided for the
latest published `0.1.x` pre-release.

| Version | Supported |
| --- | --- |
| Latest `0.1.x` pre-release | Yes |
| Older versions | No |

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private
vulnerability reporting for this repository:

https://github.com/LeonPure/portboard/security/advisories/new

Include the affected platform and version, reproduction steps, impact, and any
suggested mitigation. You should receive an acknowledgement within 72 hours.

PortBoard inspects local processes and can request process termination. Reports
involving PID reuse, confirmation bypass, command execution, unsafe URL handling,
or unintended disclosure of local process metadata are especially important.
