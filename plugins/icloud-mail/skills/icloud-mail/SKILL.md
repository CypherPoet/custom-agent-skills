---
name: icloud-mail
description: Compose, draft, and send email through the user's iCloud Mail account in Chrome when no direct iCloud Mail connector is available. Use when the user asks to send, reply to, forward, or save a draft from iCloud Mail; do not use for other email providers.
---

# iCloud Mail

Use the `control-browser` skill and its browser and authentication rules to operate [iCloud Mail](https://www.icloud.com/mail/). This skill provides a browser workflow, not credentials or direct API access.

## Authentication

- Reuse the current session only when the correct iCloud account is visibly active.
- If Apple requires sign-in, use only the browser's advertised authentication capability. Never ask the user to paste a password, verification code, recovery key, cookie, or other secret into ordinary chat, and never enter credentials through ordinary page automation.
- Do not use passkeys or security keys. Use a supported password or verification-code flow through browser authentication.
- Pause for the user when Apple requires approval on a trusted device, a CAPTCHA, account recovery, or a security choice. Do not change account-security settings or create an app-specific password.
- After sign-in, verify that iCloud Mail is available and that the intended account or sending alias is selected. Ask when the sender identity matters and is ambiguous.

## Interpret the Request

- Preserve the distinction between drafting and sending. “Write,” “compose,” or “draft” alone does not authorize clicking Send. “Send,” “email,” “reply,” or “forward” does authorize submission when the recipient and message are unambiguous.
- Never guess a recipient's address. Resolve it from reliable available context or ask the user.
- Clarify only details that materially affect the result, such as an unresolved recipient, ambiguous sending alias, unclear attachment, conflicting instructions, or uncertain draft-versus-send intent. Create a concise subject from the message when the user omits one.
- Follow the requested tone and purpose. Do not mention the automation workflow in the email.
- If the request gives only a broad intent and requires substantive wording or commitments to be invented, present the complete draft for approval before sending. Light editing of clearly supplied content does not require another confirmation.

## Compose and Verify

1. Open `https://www.icloud.com/mail/` and complete authentication if required.
2. Start a new message, or open the specified thread for a reply or forward.
3. Fill the intended From, To, Cc, Bcc, subject, body, and attachments. Add Cc, Bcc, or attachments only when requested or explicitly approved.
4. Preserve meaningful paragraph breaks and remove accidental placeholders. Do not invent facts, promises, deadlines, or attachments.
5. Re-read the visible compose fields after entry. Check every recipient, the selected sending alias, subject, body, and attachment status; account for any address changed by autocomplete.
6. If the user requested only a draft, save or leave it as a draft and report that it was not sent.

## Send Reliably

- Click Send once only after the request authorizes it and the verified message matches that request.
- Wait for observable success, such as the compose window closing with a sent confirmation. Do not report success based only on clicking the button.
- If the result is ambiguous, inspect the Sent mailbox once before considering any retry. Never retry automatically when that could create a duplicate.
- Report the outcome with the recipient list and subject. If delivery cannot be verified, say exactly what remains uncertain.

## Boundaries and Fallback

- Do not alter mail rules, signatures, contacts, aliases, preferences, or account data unless the user explicitly requests that separate change.
- Do not delete, archive, or move unrelated messages while composing or sending.
- Do not expose credentials, authentication artifacts, mailbox content, or browser-session data beyond what the user's request requires.
- If the controlled browser is unavailable or Apple blocks the sign-in or automation flow, explain the limitation and provide a polished, copyable draft rather than claiming the email was sent.
