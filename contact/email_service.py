import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from flask import jsonify, request, session, url_for, Blueprint
import re
from models.user import User
import datetime
from dotenv import load_dotenv

load_dotenv()
class EmailService:
    def __init__(self, smtp_host: str = "smtp.gmail.com", smtp_port: int = 465):
        """Initialize email service with SMTP settings."""
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.recipient_email = os.getenv("RECIPIENT_EMAIL")

        if not all([self.smtp_username, self.smtp_password, self.recipient_email]):
            raise ValueError("Missing required email configuration. Please set SMTP_USERNAME, SMTP_PASSWORD, and RECIPIENT_EMAIL environment variables.")

    def create_email_message(self, sender_name: str, sender_email: str, subject: str, message: str, to_email: str = None) -> MIMEMultipart:
        """Create email message with HTML template."""
        msg = MIMEMultipart()
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = to_email if to_email else self.recipient_email
        msg["Subject"] = subject if not subject.startswith("[Contact Form]") else f"[Contact Form] {subject}"

        # Create HTML template
        html = message if "<html>" in message else f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    {message}
                </div>
            </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))
        return msg

    def create_contact_form_message(self, sender_name: str, sender_email: str, subject: str, message: str) -> str:
        """Create HTML message for contact form submissions."""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4F46E5;">New Contact Form Submission</h2>
                    <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p><strong>From:</strong> {sender_name} ({sender_email})</p>
                        <p><strong>Subject:</strong> {subject}</p>
                        <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                            <p><strong>Message:</strong></p>
                            <p style="white-space: pre-wrap;">{message}</p>
                        </div>
                    </div>
                    <p style="color: #6b7280; font-size: 0.875rem;">
                        This message was sent from the ToolMines AI contact form.
                    </p>
                </div>
            </body>
        </html>
        """

    def send_contact_form_email(self, sender_name: str, sender_email: str, subject: str, message: str) -> tuple[bool, Optional[str]]:
        """Send contact form email."""
        html_message = self.create_contact_form_message(sender_name, sender_email, subject, message)
        return self.send_email(
            sender_name=sender_name,
            sender_email=sender_email,
            subject=f"[Contact Form] {subject}",
            message=html_message
        )

    def send_email(self, sender_name: str, sender_email: str, subject: str, message: str, to_email: str = None) -> tuple[bool, Optional[str]]:
        """Send email using SMTP server."""
        try:
            msg = self.create_email_message(sender_name, sender_email, subject, message, to_email)

            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            return True, None

        except Exception as e:
            return False, str(e)

    def send_welcome_email(self, user_email: str, user_name: str = None) -> tuple[bool, Optional[str]]:
        """Send welcome email to newly registered user."""
        subject = "Welcome to ToolMines AI!"
        
        # Create welcome message with modern HTML template
        message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #4F46E5;">Welcome to ToolMines AI!</h2>
                    <p>Dear {user_name or 'User'},</p>
                    <p>Thank you for joining ToolMines AI! We're excited to have you as part of our community.</p>
                    
                    <div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #4F46E5; margin-top: 0;">What's Next?</h3>
                        <ul style="list-style-type: none; padding: 0;">
                            <li style="margin-bottom: 10px;">✨ Explore our AI-powered tools</li>
                            <li style="margin-bottom: 10px;">🤖 Try our chatbot for instant assistance</li>
                            <li style="margin-bottom: 10px;">🗣️ Experience our voice interaction features</li>
                            <li style="margin-bottom: 10px;">🌐 Use our language translation services</li>
                        </ul>
                    </div>
                    
                    <p>Need help getting started? Feel free to:</p>
                    <ul>
                        <li>Visit our tools page to explore all features</li>
                        <li>Contact our support team if you have questions</li>
                        <li>Subscribe to our newsletter for updates</li>
                    </ul>
                    
                    <p>We're here to help you make the most of our AI tools!</p>
                    
                    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                        <p style="color: #6b7280; font-size: 0.875rem;">
                            Best regards,<br>
                            The ToolMines AI Team
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(
            sender_name="ToolMines AI",
            sender_email=self.smtp_username,
            subject=subject,
            message=message,
            to_email=user_email
        )

    

    

def create_newsletter_blueprint(email_service):
    newsletter_bp = Blueprint('newsletter', __name__)

    @newsletter_bp.route('/submit-newsletter', methods=['POST'])
    def submit_newsletter():
        try:
            # Check if user is logged in
            if 'user_id' not in session:
                return jsonify({
                    'success': False,
                    'redirect': url_for('auth.login'),
                    'message': 'Please log in to subscribe to our newsletter'
                }), 401
                
            data = request.get_json()
            subscriber_email = data.get('email')
            
            # Get logged-in user details
            logged_in_user = User.get_user_by_email(session['user_id'])
            if not logged_in_user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            if not subscriber_email:
                return jsonify({'success': False, 'message': 'Email is required'}), 400
                
            # Add email validation
            if not re.match(r"[^@]+@[^@]+\.[^@]+", subscriber_email):
                return jsonify({'success': False, 'message': 'Please enter a valid email address'}), 400
            
            # Create welcome email content for subscriber
            welcome_subject = "Welcome to ToolMines AI Newsletter!"
            welcome_message = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4F46E5;">Welcome to ToolMines AI!</h2>
                <p>Thank you for subscribing to our newsletter. We're excited to have you join our community!</p>
                <p>You'll receive regular updates about:</p>
                <ul>
                    <li>New AI tools and features</li>
                    <li>Tips and tutorials</li>
                    <li>Industry insights</li>
                    <li>Special offers</li>
                </ul>
                <p>Stay tuned for our next update!</p>
                <div style="margin-top: 20px; padding: 15px; background-color: #f3f4f6; border-radius: 5px;">
                    <p style="margin: 0; color: #6b7280; font-size: 0.9em;">
                        If you didn't subscribe to ToolMines AI newsletter, please ignore this email.
                    </p>
                </div>
            </div>
            """
            
            # Create notification email content for company
            notification_subject = "New Newsletter Subscription"
            notification_message = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4F46E5;">New Newsletter Subscriber!</h2>
                <p>A new user has subscribed to the ToolMines AI newsletter.</p>
                <div style="margin: 20px 0; padding: 15px; background-color: #f3f4f6; border-radius: 5px;">
                    <h3 style="margin-top: 0;">Subscriber Details:</h3>
                    <p><strong>Subscriber Email:</strong> {subscriber_email}</p>
                    <p><strong>Subscription Time:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Subscription Source:</strong> Website Newsletter Form</p>
                    
                    <h3 style="margin-top: 20px;">User Account Details:</h3>
                    <p><strong>Account Email:</strong> {logged_in_user.email}</p>
                    <p><strong>User Name:</strong> {logged_in_user.name or 'Not provided'}</p>
                    <p><strong>Account Type:</strong> {'Google Account' if logged_in_user.google_id else 'Email Account'}</p>
                    <p><strong>Account Created:</strong> {logged_in_user.created_at.strftime('%Y-%m-%d %H:%M:%S') if logged_in_user.created_at else 'Unknown'}</p>
                </div>
            </div>
            """
            
            # Send welcome email to subscriber
            subscriber_success, subscriber_error = email_service.send_email(
                sender_name="ToolMines AI",
                sender_email=email_service.smtp_username,
                subject=welcome_subject,
                message=welcome_message,
                to_email=subscriber_email
            )
            
            # Send notification to company
            company_success, company_error = email_service.send_email(
                sender_name="ToolMines AI System",
                sender_email=email_service.smtp_username,
                subject=notification_subject,
                message=notification_message,
                to_email=email_service.recipient_email
            )
            
            if not subscriber_success:
                return jsonify({
                    'success': False,
                    'message': f'Failed to send confirmation email: {subscriber_error}'
                }), 500
                
            if not company_success:
                # Log the error but don't return it to the user
                print(f"Failed to send company notification: {company_error}")
                
            return jsonify({
                'success': True,
                'message': 'Thank you for subscribing! Please check your email for confirmation.'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'An error occurred: {str(e)}'
            }), 500
    
    return newsletter_bp

def setup_newsletter_service(app, email_service):
    """Setup newsletter service by registering the blueprint."""
    newsletter_bp = create_newsletter_blueprint(email_service)
    app.register_blueprint(newsletter_bp)