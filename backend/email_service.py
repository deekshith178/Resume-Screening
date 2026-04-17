"""
Email notification service supporting multiple providers.

Supported providers:
- SMTP (Gmail, Outlook, custom SMTP servers)
- SendGrid
- AWS SES
- Mailgun

Falls back to logging if no provider is configured.
"""
import os
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, Literal
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)

# Try to import optional email providers
SENDGRID_AVAILABLE = False
AWS_SES_AVAILABLE = False
MAILGUN_AVAILABLE = False

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    pass

try:
    import boto3
    AWS_SES_AVAILABLE = True
except ImportError:
    pass

try:
    import requests
    MAILGUN_AVAILABLE = True
except ImportError:
    pass


class EmailService:
    """Email notification service supporting multiple providers."""
    
    def __init__(self):
        # Determine which provider to use (priority order)
        self.provider = os.getenv("EMAIL_PROVIDER", "smtp").lower()  # smtp, sendgrid, ses, mailgun
        self.from_email = os.getenv("EMAIL_FROM", os.getenv("SENDGRID_FROM_EMAIL", "noreply@example.com"))
        self.enabled = False
        self.provider_name = "none"
        
        # Initialize provider based on EMAIL_PROVIDER env var
        if self.provider == "sendgrid":
            self._init_sendgrid()
        elif self.provider == "ses":
            self._init_aws_ses()
        elif self.provider == "mailgun":
            self._init_mailgun()
        else:  # Default to SMTP
            self._init_smtp()
        
        if not self.enabled:
            logger.warning(f"Email service disabled. No provider configured. Emails will be logged only.")
    
    def _init_smtp(self):
        """Initialize SMTP provider."""
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", os.getenv("SMTP_EMAIL"))
        self.smtp_password = os.getenv("SMTP_PASSWORD", os.getenv("SMTP_PASS"))
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        if self.smtp_user and self.smtp_password:
            self.enabled = True
            self.provider_name = f"SMTP ({self.smtp_host})"
            logger.info(f"SMTP email service initialized: {self.smtp_host}:{self.smtp_port}")
        else:
            logger.warning("SMTP credentials not set. Set SMTP_USER and SMTP_PASSWORD in .env")
    
    def _init_sendgrid(self):
        """Initialize SendGrid provider."""
        if not SENDGRID_AVAILABLE:
            logger.warning("SendGrid SDK not installed. Install with: pip install sendgrid")
            return
        
        self.api_key = os.getenv("SENDGRID_API_KEY")
        if self.api_key:
            try:
                self.sendgrid_client = SendGridAPIClient(self.api_key)
                self.enabled = True
                self.provider_name = "SendGrid"
                logger.info("SendGrid email service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid: {e}")
        else:
            logger.warning("SENDGRID_API_KEY not set in environment")
    
    def _init_aws_ses(self):
        """Initialize AWS SES provider."""
        if not AWS_SES_AVAILABLE:
            logger.warning("boto3 not installed. Install with: pip install boto3")
            return
        
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if self.aws_access_key and self.aws_secret_key:
            try:
                self.ses_client = boto3.client(
                    'ses',
                    region_name=self.aws_region,
                    aws_access_key_id=self.aws_access_key,
                    aws_secret_access_key=self.aws_secret_key
                )
                self.enabled = True
                self.provider_name = f"AWS SES ({self.aws_region})"
                logger.info(f"AWS SES email service initialized: {self.aws_region}")
            except Exception as e:
                logger.error(f"Failed to initialize AWS SES: {e}")
        else:
            logger.warning("AWS credentials not set. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
    
    def _init_mailgun(self):
        """Initialize Mailgun provider."""
        if not MAILGUN_AVAILABLE:
            logger.warning("requests library not installed. Install with: pip install requests")
            return
        
        self.mailgun_api_key = os.getenv("MAILGUN_API_KEY")
        self.mailgun_domain = os.getenv("MAILGUN_DOMAIN")
        
        if self.mailgun_api_key and self.mailgun_domain:
            self.enabled = True
            self.provider_name = f"Mailgun ({self.mailgun_domain})"
            logger.info(f"Mailgun email service initialized: {self.mailgun_domain}")
        else:
            logger.warning("Mailgun credentials not set. Set MAILGUN_API_KEY and MAILGUN_DOMAIN")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email using the configured provider.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.enabled:
            # Log email instead of sending
            logger.info(f"[EMAIL] Would send email to {to_email} via {self.provider_name}")
            logger.info(f"[EMAIL] Subject: {subject}")
            logger.info(f"[EMAIL] Content: {text_content or html_content[:200]}...")
            return False
        
        try:
            if self.provider == "sendgrid":
                return self._send_via_sendgrid(to_email, subject, html_content, text_content)
            elif self.provider == "ses":
                return self._send_via_ses(to_email, subject, html_content, text_content)
            elif self.provider == "mailgun":
                return self._send_via_mailgun(to_email, subject, html_content, text_content)
            else:  # SMTP
                return self._send_via_smtp(to_email, subject, html_content, text_content)
        except Exception as e:
            logger.error(f"Error sending email to {to_email} via {self.provider_name}: {str(e)}")
            return False
    
    def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send email via SMTP."""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email
            
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)
            
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
            context = ssl.create_default_context()
            
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls(context=context)
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context)
            
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, to_email, message.as_string())
            server.quit()
            
            logger.info(f"Email sent successfully via SMTP to {to_email}")
            return True
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False
    
    def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send email via SendGrid."""
        try:
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content),
            )
            
            if text_content:
                message.add_content(Content("text/plain", text_content))
            
            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully via SendGrid to {to_email}")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} - {response.body}")
                return False
        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            return False
    
    def _send_via_ses(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send email via AWS SES."""
        try:
            message_body = {"Html": {"Data": html_content, "Charset": "UTF-8"}}
            if text_content:
                message_body["Text"] = {"Data": text_content, "Charset": "UTF-8"}
            
            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": message_body
                }
            )
            
            logger.info(f"Email sent successfully via AWS SES to {to_email}: {response['MessageId']}")
            return True
        except Exception as e:
            logger.error(f"AWS SES error: {str(e)}")
            return False
    
    def _send_via_mailgun(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send email via Mailgun."""
        try:
            url = f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages"
            data = {
                "from": self.from_email,
                "to": to_email,
                "subject": subject,
                "html": html_content,
            }
            if text_content:
                data["text"] = text_content
            
            response = requests.post(
                url,
                auth=("api", self.mailgun_api_key),
                data=data
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully via Mailgun to {to_email}")
                return True
            else:
                logger.error(f"Mailgun error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Mailgun error: {str(e)}")
            return False
    
    def send_selection_notification(
        self,
        candidate_email: str,
        candidate_name: str,
        job_title: str,
        company_name: str = "Our Company",
    ) -> bool:
        """
        Send notification to selected candidate.
        
        Args:
            candidate_email: Candidate's email address
            candidate_name: Candidate's name
            job_title: Job title they were selected for
            company_name: Company name (optional)
        
        Returns:
            True if email was sent successfully
        """
        subject = f"Congratulations! You've been selected for {job_title}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Congratulations, {candidate_name}!</h2>
                
                <p>We are pleased to inform you that you have been selected for the position of <strong>{job_title}</strong>.</p>
                
                <p>Your application stood out among many candidates, and we believe your skills and experience align perfectly with our requirements.</p>
                
                <p>Next steps:</p>
                <ul>
                    <li>Our team will contact you within the next few business days</li>
                    <li>Please keep your contact information up to date</li>
                    <li>You can view your application status in your candidate portal</li>
                </ul>
                
                <p>We look forward to welcoming you to the {company_name} team!</p>
                
                <p>Best regards,<br>
                The {company_name} Team</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Congratulations, {candidate_name}!

We are pleased to inform you that you have been selected for the position of {job_title}.

Your application stood out among many candidates, and we believe your skills and experience align perfectly with our requirements.

Next steps:
- Our team will contact you within the next few business days
- Please keep your contact information up to date
- You can view your application status in your candidate portal

We look forward to welcoming you to the {company_name} team!

Best regards,
The {company_name} Team
        """
        
        return self.send_email(candidate_email, subject, html_content, text_content)
    
    def send_guidance_email(
        self,
        candidate_email: str,
        candidate_name: str,
        guidance_data: Dict[str, Any],
        portal_url: Optional[str] = None,
    ) -> bool:
        """
        Send guidance recommendations email to candidate.
        
        Args:
            candidate_email: Candidate's email address
            candidate_name: Candidate's name
            guidance_data: Guidance data containing recommendations
            portal_url: URL to candidate portal (optional)
        
        Returns:
            True if email was sent successfully
        """
        subject = "Personalized Career Guidance and Skill Recommendations"
        
        # Extract guidance resources
        resources = guidance_data.get("resources", [])
        missing_skills = guidance_data.get("missing_skills", [])
        
        resources_html = ""
        if resources:
            resources_html = "<ul>"
            for resource in resources[:10]:  # Limit to 10 resources
                title = resource.get("title", "Resource")
                url = resource.get("url", "#")
                resource_type = resource.get("type", "Resource")
                resources_html += f'<li><strong>{resource_type}:</strong> <a href="{url}" style="color: #2563eb;">{title}</a></li>'
            resources_html += "</ul>"
        
        skills_html = ""
        if missing_skills:
            skills_html = "<ul>"
            for skill in missing_skills[:5]:  # Limit to 5 skills
                skills_html += f"<li>{skill}</li>"
            skills_html += "</ul>"
        
        portal_link = ""
        if portal_url:
            portal_link = f'<p><a href="{portal_url}" style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">View Your Portal</a></p>'
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Career Guidance for {candidate_name}</h2>
                
                <p>Thank you for your interest in our position. While we're unable to proceed with your application at this time, we've prepared personalized guidance to help you strengthen your profile.</p>
                
                {f'<h3>Recommended Skills to Develop:</h3>{skills_html}' if skills_html else ''}
                
                {f'<h3>Recommended Learning Resources:</h3>{resources_html}' if resources_html else ''}
                
                {portal_link}
                
                <p>We encourage you to continue developing your skills and wish you success in your career journey.</p>
                
                <p>Best regards,<br>
                The Hiring Team</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Career Guidance for {candidate_name}

Thank you for your interest in our position. While we're unable to proceed with your application at this time, we've prepared personalized guidance to help you strengthen your profile.

{f'Recommended Skills to Develop:\n{chr(10).join("- " + skill for skill in missing_skills[:5])}' if missing_skills else ''}

{f'Recommended Learning Resources:\n{chr(10).join("- " + r.get("title", "Resource") + ": " + r.get("url", "#") for r in resources[:10])}' if resources else ''}

{f'View your portal: {portal_url}' if portal_url else ''}

We encourage you to continue developing your skills and wish you success in your career journey.

Best regards,
The Hiring Team
        """
        
        return self.send_email(candidate_email, subject, html_content, text_content)


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the global email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service

