"""
Management command to test email configuration
"""
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test email configuration and logging'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('EMAIL CONFIGURATION TEST'))
        self.stdout.write(self.style.SUCCESS('='*60))

        self.stdout.write(f"\nEMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"DEBUG: {settings.DEBUG}")

        self.stdout.write(self.style.WARNING('\n' + '-'*60))
        self.stdout.write(self.style.WARNING('Sending test email...'))
        self.stdout.write(self.style.WARNING('-'*60 + '\n'))

        try:
            email = EmailMultiAlternatives(
                subject="Test Email - SI-SEP Sport RDC",
                body="This is a test email to verify the console backend is working.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=["test@example.com"],
            )
            email.attach_alternative(
                "<p>This is a test email to verify the console backend is working.</p>",
                "text/html"
            )
            
            result = email.send(fail_silently=False)
            self.stdout.write(self.style.SUCCESS(f'\nEmail sent successfully! Result: {result}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError sending email: {e}'))
            import traceback
            traceback.print_exc()

        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('TEST COMPLETE'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
