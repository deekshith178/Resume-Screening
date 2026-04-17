# Email Provider Configuration Guide

The email service now supports multiple providers. Choose the one that best fits your needs.

## Supported Providers

1. **SMTP** (Default) - Works with Gmail, Outlook, custom SMTP servers
2. **SendGrid** - Transactional email service
3. **AWS SES** - Amazon Simple Email Service
4. **Mailgun** - Email API service

## Configuration

Set the `EMAIL_PROVIDER` environment variable in your `.env` file to choose a provider:

```env
EMAIL_PROVIDER=smtp  # Options: smtp, sendgrid, ses, mailgun
```

---

## 1. SMTP Provider (Default)

**Best for:** Gmail, Outlook, custom SMTP servers, development/testing

### Setup

Add to `.env`:

```env
EMAIL_PROVIDER=smtp
EMAIL_FROM=noreply@yourcompany.com

# Gmail Example
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Outlook Example
# SMTP_HOST=smtp-mail.outlook.com
# SMTP_PORT=587
# SMTP_USER=your-email@outlook.com
# SMTP_PASSWORD=your-password
# SMTP_USE_TLS=true

# Custom SMTP Example
# SMTP_HOST=smtp.yourdomain.com
# SMTP_PORT=465
# SMTP_USER=noreply@yourdomain.com
# SMTP_PASSWORD=your-password
# SMTP_USE_TLS=false
```

### Gmail Setup

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to Google Account → Security → App passwords
   - Create a new app password for "Mail"
   - Use this password in `SMTP_PASSWORD`

### Outlook Setup

1. Use your Outlook email and password
2. If 2FA is enabled, use an app password

### Pros
- ✅ Free (with Gmail/Outlook)
- ✅ No API keys needed
- ✅ Works with any SMTP server
- ✅ Good for development

### Cons
- ⚠️ Gmail/Outlook have daily sending limits
- ⚠️ May require app passwords
- ⚠️ Less reliable for production

---

## 2. SendGrid Provider

**Best for:** Production applications, high volume, analytics

### Setup

1. Sign up at https://sendgrid.com
2. Create an API key with "Mail Send" permissions
3. Verify sender email address

Add to `.env`:

```env
EMAIL_PROVIDER=sendgrid
EMAIL_FROM=noreply@yourcompany.com
SENDGRID_API_KEY=your_sendgrid_api_key_here
```

### Install Dependency

```bash
pip install sendgrid>=6.10.0
```

### Pros
- ✅ Free tier: 100 emails/day
- ✅ Excellent deliverability
- ✅ Email analytics
- ✅ Easy to use

### Cons
- ⚠️ Requires API key
- ⚠️ Free tier has limits

---

## 3. AWS SES Provider

**Best for:** AWS users, high volume, cost-effective

### Setup

1. Create AWS account
2. Verify sender email/domain in SES
3. Move out of sandbox mode (if needed)
4. Create IAM user with SES permissions

Add to `.env`:

```env
EMAIL_PROVIDER=ses
EMAIL_FROM=noreply@yourdomain.com
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Install Dependency

```bash
pip install boto3>=1.28.0
```

### IAM Policy Example

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    }
  ]
}
```

### Pros
- ✅ Very cost-effective ($0.10 per 1,000 emails)
- ✅ High deliverability
- ✅ Integrates with AWS ecosystem
- ✅ Scales automatically

### Cons
- ⚠️ Requires AWS account
- ⚠️ Sandbox mode initially (verify recipients)
- ⚠️ More setup complexity

---

## 4. Mailgun Provider

**Best for:** Developers, API-first approach

### Setup

1. Sign up at https://www.mailgun.com
2. Verify your domain
3. Get API key from dashboard

Add to `.env`:

```env
EMAIL_PROVIDER=mailgun
EMAIL_FROM=noreply@yourdomain.com
MAILGUN_API_KEY=your_mailgun_api_key
MAILGUN_DOMAIN=yourdomain.com
```

### Install Dependency

```bash
pip install requests>=2.31.0  # Already installed
```

### Pros
- ✅ Free tier: 5,000 emails/month
- ✅ Great API
- ✅ Email validation features
- ✅ Good documentation

### Cons
- ⚠️ Requires domain verification
- ⚠️ Free tier has limits

---

## Quick Comparison

| Provider | Free Tier | Best For | Setup Difficulty |
|----------|-----------|----------|------------------|
| SMTP | Unlimited* | Development, Gmail users | Easy |
| SendGrid | 100/day | Production, analytics | Easy |
| AWS SES | 62,000/month** | AWS users, scale | Medium |
| Mailgun | 5,000/month | Developers, API-first | Easy |

*Gmail/Outlook have daily limits
**First 12 months, then pay-as-you-go

---

## Testing Your Configuration

### Test Email Service

```python
from backend.email_service import get_email_service

email_service = get_email_service()

# Test sending
success = email_service.send_email(
    to_email="test@example.com",
    subject="Test Email",
    html_content="<h1>Test</h1><p>This is a test email.</p>",
    text_content="Test\n\nThis is a test email."
)

print(f"Email sent: {success}")
print(f"Provider: {email_service.provider_name}")
```

### Check Logs

The service will log which provider is being used:

```
INFO: SMTP email service initialized: smtp.gmail.com:587
INFO: Email sent successfully via SMTP to test@example.com
```

---

## Fallback Behavior

If no provider is configured or all fail, the service will:
- Log email details instead of sending
- Continue normal operation without errors
- Return `False` from `send_email()`

Check logs for:
```
[EMAIL] Would send email to candidate@example.com via none
```

---

## Switching Providers

To switch providers, simply change `EMAIL_PROVIDER` in `.env`:

```env
# Switch from SMTP to SendGrid
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your_key
```

No code changes needed! The service automatically detects and uses the new provider.

---

## Troubleshooting

### SMTP Issues

- **"Authentication failed"**: Check username/password, use app password for Gmail
- **"Connection refused"**: Check SMTP_HOST and SMTP_PORT
- **"TLS error"**: Try `SMTP_USE_TLS=false` for port 465

### SendGrid Issues

- **"Unauthorized"**: Check API key permissions
- **"Sender not verified"**: Verify sender email in SendGrid dashboard

### AWS SES Issues

- **"Email address not verified"**: Verify sender email in SES console
- **"Sandbox mode"**: Request production access or verify recipient emails

### Mailgun Issues

- **"Domain not found"**: Verify domain in Mailgun dashboard
- **"Unauthorized"**: Check API key

---

## Production Recommendations

1. **Use a dedicated email service** (SendGrid, SES, or Mailgun) for production
2. **Verify your domain** for better deliverability
3. **Monitor email delivery** rates
4. **Set up SPF/DKIM records** for your domain
5. **Implement retry logic** for failed sends
6. **Log email events** for audit purposes

---

## Environment Variables Summary

### Common (All Providers)
```env
EMAIL_PROVIDER=smtp|sendgrid|ses|mailgun
EMAIL_FROM=noreply@yourcompany.com
```

### SMTP Only
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
```

### SendGrid Only
```env
SENDGRID_API_KEY=your_key
```

### AWS SES Only
```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### Mailgun Only
```env
MAILGUN_API_KEY=your_key
MAILGUN_DOMAIN=yourdomain.com
```


