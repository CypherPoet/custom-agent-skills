# icloud-mail

Compose and send email through iCloud Mail in a controlled browser session.

This is browser automation rather than an Apple Mail API integration. It can reuse an authenticated browser session and request a supported sign-in flow when necessary, but Apple may still require the user to complete two-factor authentication, a trusted-device prompt, or another interactive security check.

This plugin currently targets Codex and ChatGPT environments that provide the controlled-browser capability.

## Installation

Install via the [`cypherpoet-toolchest`](https://github.com/CypherPoet/cypherpoet-toolchest) marketplace:

```shell
codex plugin marketplace add CypherPoet/cypherpoet-toolchest
codex plugin add icloud-mail@cypherpoet-toolchest
```

## Skills

| Skill | Description | Model-Invocable |
|---|---|---|
| [icloud-mail](skills/icloud-mail/SKILL.md) | Compose, draft, and send email through iCloud Mail in Chrome. | Yes |
