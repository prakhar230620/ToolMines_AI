from dataclasses import dataclass
from typing import Optional
from .email_service import EmailService
import re
from flask import jsonify, request, session, url_for, Blueprint, redirect
from models.user import User
import datetime
from config.database import db
import pandas as pd
import io
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ContactForm:
    """Data class to store contact form data."""
    name: str
    email: str
    subject: str
    message: str

class ContactHandler:
    """Handler for processing contact form submissions."""
    
    def __init__(self):
        self.email_service = EmailService()

    def validate_email(self, email: str) -> bool:
        """Validate email format using regex pattern."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def validate_form(self, form: ContactForm) -> tuple[bool, Optional[str]]:
        """Validate contact form data."""
        if not form.name or len(form.name.strip()) < 2:
            return False, "Please enter a valid name (minimum 2 characters)"
        
        if not form.subject or len(form.subject.strip()) < 3:
            return False, "Please enter a valid subject (minimum 3 characters)"
        
        if not form.message or len(form.message.strip()) < 10:
            return False, "Please enter a message (minimum 10 characters)"
        
        return True, None

    def process_contact_form(self, form_data: ContactForm, user=None) -> tuple[bool, Optional[str]]:
        """Process contact form submission."""
        # Validate form
        is_valid, error = self.validate_form(form_data)
        if not is_valid:
            return False, error

        try:
            # Create message with user details if available
            message = form_data.message.strip()
            if user:
                user_details = f"""
----------------------------------------
Sent by User:<br>
Name: {user.name}<br>
Account Email: {user.email} <br>
Account Type: {'Google Account' if user.google_id else 'Email Account'}<br>
Account Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}<br>
----------------------------------------"""
                message = f"{message}\n\n{user_details}"

            # Send email
            success, error = self.email_service.send_email(
                sender_name=form_data.name,
                sender_email=form_data.email,
                subject=form_data.subject,
                message=message
            )

            if not success:
                return False, f"Failed to send email: {error}"

            return True, None

        except Exception as e:
            return False, f"An error occurred: {str(e)}"
def setup_contactform_routes(app):
    contact_handler = ContactHandler()
    @app.route('/submit-contact', methods=['GET', 'POST'])
    def submit_contact():
        """Handle contact form submission."""
        if request.method == 'GET':
            # If it's a GET request after login, redirect to contact page
            return redirect(url_for('contact'))
        
        if 'user_id' not in session:
            # Store the current URL in session before redirecting
            session['next_url'] = url_for('submit_contact')
            return redirect(url_for('auth.login'))

        try:
            # Create ContactForm object from request data
            form_data = ContactForm(
                name=request.form.get('name'),
                email=request.form.get('email'),
                subject=request.form.get('subject'),
                message=request.form.get('message')
            )

            # Get logged-in user details
            logged_in_user = User.get_user_by_email(session['user_id'])
            if not logged_in_user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404

            # Process the contact form
            success, error = contact_handler.process_contact_form(form_data, logged_in_user)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'Thank you for your message! We will get back to you soon.'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Error: {error}'
                }), 400

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'An unexpected error occurred: {str(e)}'
            }), 500
