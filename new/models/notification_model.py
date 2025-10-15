# models/notification_model.py
import requests
from datetime import datetime
from config import Config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationModel:
    @staticmethod
    def send_email_notification(to_email, subject, message, user_name=""):
        """
        Send email using Gmail SMTP (Easy & Free)
        What this does: Sends professional emails about adoption status
        Why: Users need to know when their application status changes
        """
        try:
            # Gmail SMTP configuration
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            
            # Your Gmail credentials (use App Password, not regular password)
            from_email = Config.EMAIL_USER  # Your Gmail
            from_password = Config.EMAIL_PASSWORD  # Your Gmail App Password
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # HTML email body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #2c3e50; text-align: center;">🐾 Pet Adoption Update</h2>
                    <p>Hello {user_name},</p>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        {message}
                    </div>
                    <p>Thank you for using our pet adoption service!</p>
                    <hr style="border: 1px solid #eee;">
                    <p style="font-size: 12px; color: #666; text-align: center;">
                        This is an automated message from Pet Adoption System
                    </p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(from_email, from_password)
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            print(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    @staticmethod
    def send_sms_notification(to_phone, message):
        """
        Send SMS using Twilio (Modern & Reliable)
        What this does: Sends SMS about adoption status updates
        Why: Instant notification for important updates
        """
        try:
            from twilio.rest import Client
            
            # Twilio credentials
            account_sid = Config.TWILIO_ACCOUNT_SID
            auth_token = Config.TWILIO_AUTH_TOKEN
            from_phone = Config.TWILIO_PHONE_NUMBER
            
            client = Client(account_sid, auth_token)
            
            # Send SMS
            message = client.messages.create(
                body=f"🐾 Pet Adoption Update: {message}",
                from_=from_phone,
                to=to_phone
            )
            
            print(f"SMS sent successfully to {to_phone}, SID: {message.sid}")
            return True
            
        except Exception as e:
            print(f"SMS sending failed: {e}")
            return False
    
    @staticmethod
    def send_adoption_status_notification(application_data, old_status, new_status):
        """
        Send notification when adoption status changes
        What this does: Automatically notifies users of status changes
        Why: Users should know immediately when status updates
        """
        try:
            user_name = application_data.get('applicant_name', 'Adopter')
            user_email = application_data.get('email')
            user_phone = application_data.get('phone')
            pet_name = application_data.get('pet_name', 'Pet')
            
            # Create status-specific messages
            status_messages = {
                'approved': {
                    'subject': f'🎉 Your adoption application for {pet_name} has been APPROVED!',
                    'email_body': f"""
                        <h3 style="color: #27ae60;">Congratulations! Your application has been approved!</h3>
                        <p><strong>Pet:</strong> {pet_name}</p>
                        <p><strong>Status:</strong> APPROVED ✅</p>
                        <p>The shelter will contact you soon to arrange the adoption process. Please have your ID and any required documents ready.</p>
                        <p style="color: #27ae60;"><strong>Next steps:</strong> Wait for shelter contact within 24-48 hours.</p>
                    """,
                    'sms_body': f"Great news! Your adoption application for {pet_name} has been APPROVED! The shelter will contact you soon. 🎉"
                },
                'rejected': {
                    'subject': f'Update on your adoption application for {pet_name}',
                    'email_body': f"""
                        <h3 style="color: #e74c3c;">Application Update</h3>
                        <p><strong>Pet:</strong> {pet_name}</p>
                        <p><strong>Status:</strong> Not approved at this time</p>
                        <p>Unfortunately, your application was not selected for this pet. This doesn't reflect on you personally - many factors influence adoption decisions.</p>
                        <p style="color: #3498db;"><strong>Don't give up!</strong> There are many other wonderful pets looking for homes. Keep browsing our available pets!</p>
                        {f"<p><strong>Shelter notes:</strong> {application_data.get('review_notes', '')}</p>" if application_data.get('review_notes') else ''}
                    """,
                    'sms_body': f"Your application for {pet_name} was not selected this time. Don't give up - check out other amazing pets available for adoption!"
                },
                'under_review': {
                    'subject': f'Your adoption application for {pet_name} is under review',
                    'email_body': f"""
                        <h3 style="color: #f39c12;">Application Under Review</h3>
                        <p><strong>Pet:</strong> {pet_name}</p>
                        <p><strong>Status:</strong> Under Review 🔍</p>
                        <p>Great news! The shelter is now reviewing your application. They'll carefully consider all aspects of your application.</p>
                        <p><strong>Typical review time:</strong> 2-5 business days</p>
                        <p>We'll notify you as soon as there's an update!</p>
                    """,
                    'sms_body': f"Your application for {pet_name} is now under review! You'll hear back within 2-5 business days."
                }
            }
            
            # Get message content
            message_content = status_messages.get(new_status)
            if not message_content:
                return False
            
            # Send Email
            email_sent = False
            if user_email:
                email_sent = NotificationModel.send_email_notification(
                    to_email=user_email,
                    subject=message_content['subject'],
                    message=message_content['email_body'],
                    user_name=user_name
                )
            
            # Send SMS
            sms_sent = False
            if user_phone:
                sms_sent = NotificationModel.send_sms_notification(
                    to_phone=user_phone,
                    message=message_content['sms_body']
                )
            
            # Log notification attempt
            print(f"Notification sent for application {application_data.get('application_id')}: Email: {email_sent}, SMS: {sms_sent}")
            
            return email_sent or sms_sent
            
        except Exception as e:
            print(f"Notification sending failed: {e}")
            return False
    
    @staticmethod
    def send_welcome_email(user_data):
        """
        Send welcome email to new users
        What this does: Welcomes new users and explains how to use the system
        Why: Good user experience starts with proper onboarding
        """
        try:
            user_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}"
            user_email = user_data.get('email')
            user_role = user_data.get('role', 'user')
            
            role_specific_content = {
                'adopter': """
                    <p>As an adopter, you can:</p>
                    <ul>
                        <li>Browse available pets</li>
                        <li>Submit adoption applications</li>
                        <li>Track your application status</li>
                        <li>Get personalized pet recommendations</li>
                    </ul>
                    <p><strong>Ready to find your perfect companion? Start browsing pets now!</strong></p>
                """,
                'shelter_staff': """
                    <p>As shelter staff, you can:</p>
                    <ul>
                        <li>Manage your shelter's pets</li>
                        <li>Review adoption applications</li>
                        <li>Approve or decline applications</li>
                        <li>Update pet information</li>
                    </ul>
                    <p><strong>Ready to help pets find homes? Check your pending applications!</strong></p>
                """,
                'admin': """
                    <p>As an admin, you have full access to:</p>
                    <ul>
                        <li>Manage all pets across all shelters</li>
                        <li>Oversee all adoption applications</li>
                        <li>Manage users and shelters</li>
                        <li>Access system analytics</li>
                    </ul>
                    <p><strong>Ready to manage the system? Access your admin dashboard!</strong></p>
                """
            }
            
            welcome_message = f"""
                <h3 style="color: #27ae60;">Welcome to Pet Adoption System! 🐾</h3>
                <p>Thank you for joining our mission to help pets find loving homes.</p>
                {role_specific_content.get(user_role, '')}
                <p><strong>Need help?</strong> Contact our support team anytime.</p>
                <p>Happy pet finding!</p>
            """
            
            return NotificationModel.send_email_notification(
                to_email=user_email,
                subject="🐾 Welcome to Pet Adoption System!",
                message=welcome_message,
                user_name=user_name
            )
            
        except Exception as e:
            print(f"Welcome email failed: {e}")
            return False