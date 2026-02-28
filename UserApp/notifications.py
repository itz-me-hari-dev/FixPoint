from django.conf import settings
from django.core.mail import send_mail


def _send_notification(subject, message, recipients):
    valid_recipients = list(dict.fromkeys(email for email in recipients if email))
    if not valid_recipients:
        return

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=valid_recipients,
        fail_silently=True,
    )


def notify_contact_message(form_type, full_name, email, message):
    if not email:
        return

    subject = f"FixPoint: We received your {form_type} message"
    body = (
        f"Hi {full_name},\n\n"
        f"We received your {form_type} message on FixPoint.\n"
        f"Our team will review it and get back to you if needed.\n\n"
        f"Your message:\n{message}\n\n"
        f"Thanks,\nFixPoint Team"
    )
    _send_notification(subject, body, [email])


def notify_booking_created(booking):
    customer_email = booking.customer.user.user.email
    provider_email = booking.service_provider.user.user.email

    subject = f"New booking request #{booking.id}"
    customer_body = (
        f"Your booking request #{booking.id} has been sent to "
        f"{booking.service_provider.full_name}."
    )
    provider_body = (
        f"You have received a new booking request #{booking.id} "
        f"from {booking.customer.full_name}."
    )

    if customer_email == provider_email:
        merged_body = (
            f"{customer_body}\n\n"
            f"{provider_body}"
        )
        _send_notification(subject, merged_body, [customer_email])
    else:
        _send_notification(subject, customer_body, [customer_email])
        _send_notification(subject, provider_body, [provider_email])


def notify_booking_status_updated(booking):
    customer_email = booking.customer.user.user.email
    provider_email = booking.service_provider.user.user.email
    status_label = booking.status.replace("_", " ").title()

    subject = f"Booking #{booking.id} is now {status_label}"
    customer_body = (
        f"Your booking #{booking.id} has been updated to {status_label}."
    )
    provider_body = (
        f"Booking #{booking.id} with {booking.customer.full_name} "
        f"is now {status_label}."
    )

    if customer_email == provider_email:
        merged_body = (
            f"{customer_body}\n\n"
            f"{provider_body}"
        )
        _send_notification(subject, merged_body, [customer_email])
    else:
        _send_notification(subject, customer_body, [customer_email])
        _send_notification(subject, provider_body, [provider_email])


def notify_job_completed(booking):
    customer_email = booking.customer.user.user.email
    provider_email = booking.service_provider.user.user.email

    subject = f"Job completed for booking #{booking.id}"
    body = (
        f"Booking #{booking.id} has been marked as completed.\n"
        f"Total amount: INR {booking.total_amount}"
    )

    _send_notification(subject, body, [customer_email, provider_email])


def notify_payment_success(payment):
    booking = payment.booking
    customer_email = booking.customer.user.user.email
    provider_email = booking.service_provider.user.user.email

    subject = f"Payment successful for booking #{booking.id}"
    body = (
        f"Payment received for booking #{booking.id}.\n"
        f"Amount: INR {payment.amount}\n"
        f"Payment ID: {payment.razorpay_payment_id or 'N/A'}"
    )

    _send_notification(subject, body, [customer_email, provider_email])


def notify_provider_approval(provider, is_approved):
    provider_email = provider.user.user.email
    if is_approved:
        subject = "Your FixPoint provider profile is approved"
        body = "Your service provider profile has been approved by admin."
    else:
        subject = "Your FixPoint provider profile is rejected"
        body = (
            "Your service provider profile has been rejected by admin.\n"
            f"Reason: {provider.rejection_reason or 'Not provided'}"
        )

    _send_notification(subject, body, [provider_email])
