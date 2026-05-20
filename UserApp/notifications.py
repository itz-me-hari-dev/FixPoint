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
    status_key = booking.status
    status_label = status_key.replace("_", " ").title()

    customer_subject_map = {
        "ACCEPTED": f"FixPoint: Provider accepted booking #{booking.id}",
        "CANCELLED": f"FixPoint: Booking #{booking.id} was declined",
        "IN_PROGRESS": f"FixPoint: Work started for booking #{booking.id}",
        "COMPLETED": f"FixPoint: Booking #{booking.id} completed",
    }
    provider_subject_map = {
        "ACCEPTED": f"FixPoint: You accepted booking #{booking.id}",
        "CANCELLED": f"FixPoint: You declined booking #{booking.id}",
        "IN_PROGRESS": f"FixPoint: Work started for booking #{booking.id}",
        "COMPLETED": f"FixPoint: Booking #{booking.id} completed",
    }

    customer_message_map = {
        "ACCEPTED": (
            f"Hi {booking.customer.full_name},\n\n"
            f"Great news. {booking.service_provider.full_name} accepted your booking request "
            f"(#{booking.id}).\n\n"
            f"You can track updates from your dashboard.\n\n"
            f"Thanks,\nFixPoint Team"
        ),
        "CANCELLED": (
            f"Hi {booking.customer.full_name},\n\n"
            f"Your booking request #{booking.id} was declined by "
            f"{booking.service_provider.full_name}.\n\n"
            f"You can choose another provider from the service list.\n\n"
            f"Thanks,\nFixPoint Team"
        ),
        "IN_PROGRESS": (
            f"Hi {booking.customer.full_name},\n\n"
            f"Your service booking #{booking.id} is now in progress.\n\n"
            f"You can monitor the latest status in your dashboard.\n\n"
            f"Thanks,\nFixPoint Team"
        ),
        "COMPLETED": (
            f"Hi {booking.customer.full_name},\n\n"
            f"Your booking #{booking.id} has been marked as completed.\n\n"
            f"You can proceed with payment from your dashboard.\n\n"
            f"Thanks,\nFixPoint Team"
        ),
    }
    provider_message_map = {
        "ACCEPTED": (
            f"Hi {booking.service_provider.full_name},\n\n"
            f"You accepted booking #{booking.id} from {booking.customer.full_name}.\n\n"
            f"Please proceed as per schedule.\n\n"
            f"Thanks,\nFixPoint Team"
        ),
        "CANCELLED": (
            f"Hi {booking.service_provider.full_name},\n\n"
            f"You declined booking #{booking.id} from {booking.customer.full_name}.\n\n"
            f"No further action is required.\n\n"
            f"Thanks,\nFixPoint Team"
        ),
        "IN_PROGRESS": (
            f"Hi {booking.service_provider.full_name},\n\n"
            f"Booking #{booking.id} with {booking.customer.full_name} is marked in progress.\n\n"
            f"Update status promptly when work is completed.\n\n"
            f"Thanks,\nFixPoint Team"
        ),
        "COMPLETED": (
            f"Hi {booking.service_provider.full_name},\n\n"
            f"Booking #{booking.id} is marked completed.\n\n"
            f"The customer can now make payment.\n\n"
            f"Thanks,\nFixPoint Team"
        ),
    }

    customer_subject = customer_subject_map.get(
        status_key, f"FixPoint: Booking #{booking.id} updated"
    )
    provider_subject = provider_subject_map.get(
        status_key, f"FixPoint: Booking #{booking.id} updated"
    )
    customer_body = customer_message_map.get(
        status_key,
        f"Hi {booking.customer.full_name},\n\n"
        f"Your booking #{booking.id} status changed to {status_label}.\n\n"
        f"Thanks,\nFixPoint Team",
    )
    provider_body = provider_message_map.get(
        status_key,
        f"Hi {booking.service_provider.full_name},\n\n"
        f"Booking #{booking.id} status changed to {status_label}.\n\n"
        f"Thanks,\nFixPoint Team",
    )

    if customer_email == provider_email:
        merged_body = (
            f"{customer_body}\n\n"
            f"{provider_body}"
        )
        _send_notification(customer_subject, merged_body, [customer_email])
    else:
        _send_notification(customer_subject, customer_body, [customer_email])
        _send_notification(provider_subject, provider_body, [provider_email])


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
