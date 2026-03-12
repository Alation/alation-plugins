# SMTP Tools Guide

SMTP tools allow agents to send emails.

## Overview

SMTP tools enable:
- Sending notification emails
- Alert emails
- Report distribution
- Automated communications

## Configuration Structure

```json
{
  "name": "Display Name",
  "description": "What this tool does (shown to LLM)",
  "function_name": "unique_function_name",
  "tool_type": "SMTP",
  "smtp_config": {
    "host": "smtp.example.com",
    "port": 587,
    "use_starttls": true,
    "sender_email": "noreply@example.com"
  },
  "auth_config": {
    "auth_type": "BASIC",
    "username": "smtp_user",
    "password": "smtp_password"
  }
}
```

## SMTP Configuration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `host` | string | required | SMTP server hostname |
| `port` | integer | 587 | SMTP server port (1-65535) |
| `use_starttls` | boolean | true | Use STARTTLS encryption |
| `sender_email` | string | required | From address for emails |

## Common SMTP Servers

| Provider | Host | Port | Notes |
|----------|------|------|-------|
| SendGrid | smtp.sendgrid.net | 587 | Use "apikey" as username |
| AWS SES | email-smtp.{region}.amazonaws.com | 587 | Use IAM credentials |
| Gmail | smtp.gmail.com | 587 | Requires app password |
| Microsoft 365 | smtp.office365.com | 587 | Modern auth may be required |
| Mailgun | smtp.mailgun.org | 587 | API key as password |

## Authentication

SMTP tools currently only support BASIC authentication:

```json
{
  "auth_type": "BASIC",
  "username": "your-username",
  "password": "your-password"
}
```

**Provider-specific usernames:**
- SendGrid: Use `"apikey"` as username, API key as password
- AWS SES: Use SMTP credentials from IAM
- Gmail: Email address, app password
- Mailgun: `"postmaster@your-domain.mailgun.org"`

## Generated Tool Parameters

The SMTP tool automatically generates these input parameters:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | string | Yes | Recipient email address |
| `subject` | string | Yes | Email subject line |
| `body` | string | Yes | Email body content |
| `cc` | string | No | CC recipients |
| `bcc` | string | No | BCC recipients |

## Examples

### SendGrid Configuration

```json
{
  "name": "SendGrid Email",
  "description": "Send emails via SendGrid",
  "function_name": "send_email_sendgrid",
  "tool_type": "SMTP",
  "smtp_config": {
    "host": "smtp.sendgrid.net",
    "port": 587,
    "use_starttls": true,
    "sender_email": "notifications@mycompany.com"
  },
  "auth_config": {
    "auth_type": "BASIC",
    "username": "apikey",
    "password": "SG.xxxxxxxxxx..."
  }
}
```

### AWS SES Configuration

```json
{
  "name": "AWS SES Email",
  "description": "Send emails via AWS SES",
  "function_name": "send_email_ses",
  "tool_type": "SMTP",
  "smtp_config": {
    "host": "email-smtp.us-west-2.amazonaws.com",
    "port": 587,
    "use_starttls": true,
    "sender_email": "noreply@mycompany.com"
  },
  "auth_config": {
    "auth_type": "BASIC",
    "username": "AKIAIOSFODNN7EXAMPLE",
    "password": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
  }
}
```

### Gmail Configuration

```json
{
  "name": "Gmail Sender",
  "description": "Send emails via Gmail",
  "function_name": "send_email_gmail",
  "tool_type": "SMTP",
  "smtp_config": {
    "host": "smtp.gmail.com",
    "port": 587,
    "use_starttls": true,
    "sender_email": "myaccount@gmail.com"
  },
  "auth_config": {
    "auth_type": "BASIC",
    "username": "myaccount@gmail.com",
    "password": "xxxx xxxx xxxx xxxx"  // App password
  }
}
```

**Note:** Gmail requires an App Password when 2FA is enabled. Generate one at:
https://myaccount.google.com/apppasswords

## Security Considerations

1. **TLS Encryption** - Always use `use_starttls: true` for security
2. **Credential Storage** - Passwords are encrypted at rest
3. **Verified Sender** - Ensure sender_email is verified with your provider
4. **Rate Limits** - Be aware of provider sending limits
5. **SPF/DKIM** - Configure DNS for deliverability

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | Wrong host/port | Verify SMTP server settings |
| Authentication failed | Bad credentials | Check username/password |
| TLS handshake error | STARTTLS issue | Verify port and TLS settings |
| Sender not verified | Unverified email | Verify sender with provider |
| Rate limited | Too many emails | Reduce sending frequency |
| Blocked | Spam filters | Check content and reputation |

## Best Practices

1. **Use a dedicated sending service** - SendGrid, AWS SES, or Mailgun provide better deliverability
2. **Set up SPF and DKIM** - Improves email deliverability
3. **Monitor bounces** - Handle invalid addresses
4. **Rate limit** - Don't overwhelm recipients or hit provider limits
5. **Clear descriptions** - Help the LLM understand when to use email
