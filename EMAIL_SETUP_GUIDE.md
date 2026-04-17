# Email Notification Setup Guide

## Overview

The email notification system supports **multiple email providers**. Choose the one that best fits your needs:

- **SMTP** (Default) - Gmail, Outlook, or custom SMTP servers
- **SendGrid** - Transactional email service
- **AWS SES** - Amazon Simple Email Service  
- **Mailgun** - Email API service

The system will automatically send emails to candidates when:
- Job results are published (selected candidates)
- Guidance recommendations are sent

## Quick Start

### Option 1: SMTP (Gmail/Outlook) - Easiest for Development

Add to `.env`:

```env
EMAIL_PROVIDER=smtp
EMAIL_FROM=your-email@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
```

**For Gmail:** Enable 2FA and create an App Password in Google Account settings.

### Option 2: SendGrid - Best for Production

1. Sign up at https://sendgrid.com
2. Create API key with "Mail Send" permissions
3. Add to `.env`:

```env
EMAIL_PROVIDER=sendgrid
EMAIL_FROM=noreply@yourcompany.com
SENDGRID_API_KEY=your_api_key_here
```

4. Install: `pip install sendgrid>=6.10.0`

### Option 3: AWS SES - Best for AWS Users

```env
EMAIL_PROVIDER=ses
EMAIL_FROM=noreply@yourdomain.com
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

4. Install: `pip install boto3>=1.28.0`

### Option 4: Mailgun - Best for Developers

```env
EMAIL_PROVIDER=mailgun
EMAIL_FROM=noreply@yourdomain.com
MAILGUN_API_KEY=your_key
MAILGUN_DOMAIN=yourdomain.com
```

## Detailed Configuration

For detailed setup instructions for each provider, see **[EMAIL_PROVIDERS_GUIDE.md](./EMAIL_PROVIDERS_GUIDE.md)**

## Usage

### Automatic Email Sending

Emails are sent automatically when:

1. **Publishing Job Results:**
   ```python
   POST /jobs/{job_id}/publish
   {
     "notify_candidates": true
   }
   ```
   - Sends selection notification to all selected candidates

2. **Sending Guidance:**
   ```python
   POST /candidates/{candidate_id}/send-guidance
   {
     "job_id": "job-123",
     "channel": "email"
   }
   ```
   - Sends personalized guidance email with learning resources

### Fallback Behavior

If SendGrid is not configured (no API key or SDK not installed), the system will:
- Log email details instead of sending
- Continue normal operation without errors
- Return success status (emails logged, not sent)

Check logs for:
```
[EMAIL] Would send email to candidate@example.com
[EMAIL] Subject: ...
[EMAIL] Content: ...
```

## Testing

### Test Email Service

You can test the email service directly:

```python
from backend.email_service import get_email_service

email_service = get_email_service()

# Test selection notification
email_service.send_selection_notification(
    candidate_email="test@example.com",
    candidate_name="Test Candidate",
    job_title="Software Engineer",
    company_name="Test Company"
)

# Test guidance email
email_service.send_guidance_email(
    candidate_email="test@example.com",
    candidate_name="Test Candidate",
    guidance_data={
        "resources": [
            {"title": "Python Course", "url": "https://example.com", "type": "Course"}
        ],
        "missing_skills": ["Python", "Docker"]
    }
)
```

### Test in Development

1. Set up SendGrid with a test account
2. Use your own email address as the test recipient
3. Publish a job result or send guidance
4. Check your email inbox

## Email Templates

### Selection Notification

**Subject:** "Congratulations! You've been selected for {job_title}"

**Content:**
- Congratulations message
- Job title
- Next steps information
- Portal link (optional)

### Guidance Email

**Subject:** "Personalized Career Guidance and Skill Recommendations"

**Content:**
- Personalized message
- Missing skills list
- Recommended learning resources (courses, tutorials, etc.)
- Portal link (optional)

## Troubleshooting

### Emails Not Sending

1. **Check API Key:**
   - Verify `SENDGRID_API_KEY` is set in `.env`
   - Ensure API key has "Mail Send" permissions

2. **Check Sender Email:**
   - Verify `SENDGRID_FROM_EMAIL` is set
   - Ensure sender email is verified in SendGrid

3. **Check Logs:**
   - Look for error messages in application logs
   - Check SendGrid dashboard for delivery status

4. **Test API Key:**
   ```bash
   curl -X POST https://api.sendgrid.com/v3/mail/send \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"personalizations":[{"to":[{"email":"test@example.com"}]}],"from":{"email":"noreply@yourcompany.com"},"subject":"Test","content":[{"type":"text/plain","value":"Test email"}]}'
   ```

### SendGrid Not Installed

If SendGrid SDK is not installed, the system will log emails instead of sending them. Install with:
```bash
pip install sendgrid>=6.10.0
```

### Rate Limits

SendGrid Free Tier:
- 100 emails per day
- Upgrade plan for higher limits

Check your SendGrid dashboard for usage statistics.

## Production Considerations

1. **Domain Authentication:**
   - Set up domain authentication in SendGrid
   - Improves deliverability
   - Required for high-volume sending

2. **Email Templates:**
   - Customize email templates in `backend/email_service.py`
   - Add your company branding
   - Include unsubscribe links if required

3. **Error Handling:**
   - Monitor failed email deliveries
   - Implement retry logic if needed
   - Log email events for audit

4. **Compliance:**
   - Include unsubscribe links (required in many jurisdictions)
   - Follow CAN-SPAM, GDPR, and other regulations
   - Respect opt-out preferences

## Alternative Email Services

If you prefer a different email service, modify `backend/email_service.py`:

- **AWS SES:** Use boto3
- **Mailgun:** Use mailgun library
- **SMTP:** Use Python's smtplib
- **Postmark:** Use postmark library

The interface remains the same; just change the implementation.

