from django.shortcuts import render
from edudream.modules.utils import send_email, translate_email, decrypt_text, get_site_details


def parent_class_creation_email(classroom, lang):
    email = classroom.student.parent.user.email
    first_name = classroom.student.parent.first_name()
    student_name = str(classroom.student.get_full_name()).upper()
    tutor_name = classroom.tutor.first_name
    subject = str(classroom.subjects.name).upper()
    amount = classroom.amount
    if not first_name:
        first_name = "EduDream Parent"

    message = f"Dear {first_name}, <br><br>Your child/ward: <strong>{student_name}</strong> just created a classroom " \
              f"with a tutor <br>Tutor Name: <strong>{tutor_name}</strong><br>Subject: <strong>{subject}</strong>" \
              f"<br>Amount: <strong>{amount}</strong>"
    subject = "New Class Room Request"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def tutor_class_creation_email(classroom, lang):
    email = classroom.tutor.email
    student_name = str(classroom.student.get_full_name()).upper()
    tutor_name = classroom.tutor.first_name
    if not tutor_name:
        tutor_name = "EduDream Tutor"

    message = f"Dear {tutor_name}, <br><br>You have a new classroom request from <strong>{student_name}</strong>" \
              f"<br>Kindly login to your dashboard to accept or decline the request."
    subject = "New Class Room Request"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def tutor_class_approved_email(classroom, lang):
    email = classroom.tutor.email
    class_name = classroom.name
    link = classroom.meeting_link
    amount = classroom.amount
    student_name = str(classroom.student.get_full_name()).upper()
    tutor_name = classroom.tutor.first_name
    if not tutor_name:
        tutor_name = "EduDream Tutor"

    message = f"Dear {tutor_name}, <br><br>Classroom request accepted with " \
              f"<strong>{student_name}</strong><br>Class Name: <strong>{class_name}</strong><br>Class Link: " \
              f"<strong>{link}</strong><br>Class Fee: <strong>{amount}</strong>"
    subject = "Classroom Request Approved"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def student_class_approved_email(classroom, lang):
    email = classroom.student.parent.user.email
    class_name = classroom.name
    link = classroom.meeting_link
    student_name = str(classroom.student.first_name())
    tutor_name = classroom.tutor.get_full_name()
    if not student_name:
        student_name = "EduDream Student"

    message = f"Dear {student_name}, <br><br>Your request to start the following class was approved." \
              f"<br>Class Name: <strong>{class_name}</strong><br>Class Link: " \
              f"<strong>{link}</strong><br>Tutor Name: <strong>{tutor_name}</strong>"
    subject = "Classroom Request Approved"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def student_class_declined_email(classroom, lang):
    email = classroom.student.parent.user.email
    class_name = classroom.name
    reason = classroom.decline_reason
    student_name = str(classroom.student.first_name())
    if not student_name:
        student_name = "EduDream Student"

    message = f"Dear {student_name}, <br><br>Your request to start the following class was declined" \
              f"<br>Class Name: <strong>{class_name}</strong>" \
              f"<br>Status: <strong>DECLINED</strong>" \
              f"<br>Decline Reason: <strong>{reason}</strong>"
    subject = "Classroom Request Declined!"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def tutor_register_email(user, lang):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Tutor"

    message = f"Dear {name}, <br><br>You have successfully registered on Edudream as a Tutor" \
              f"<br>Your account is under review, and will be active shortly."
    subject = "Signup Successful"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def tutor_status_email(user):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Tutor"

    message = f"Dear {name}, <br><br>Your Tutor profile on EduDream is now active" \
              f"<br>Please login to your dashboard to complete or update your profile"
    subject = "Account Activated"
    translated_content = translate_email(message, "fr")
    translated_subject = translate_email(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def parent_register_email(user, lang):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Parent"

    message = f"Dear {name}, <br><br>You have successfully registered on Edudream as a Parent" \
              f"<br>Please login to your dashboard to add your child/ward"
    subject = "Signup Successful"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def parent_class_cancel_email(user, amount, lang):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Parent"

    message = f"Dear {name}, <br><br>A classroom was cancelled and {amount} coins have been refunded to your wallet" \
              f"<br>Please login to your dashboard to confirm"
    subject = "Cancelled Class"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def student_class_cancel_email(user, classroom, lang):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Student"

    message = f"Dear {name}, <br><br>A classroom was cancelled by your tutor" \
              f"<br>Class Name: <strong>{classroom.name}</strong>" \
              f"<br>Tutor Name: <strong>{classroom.tutor.get_full_name()}</strong>"
    subject = "Cancelled Class"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def parent_low_threshold_email(user, amount, lang):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Parent"

    message = f"Dear {name}, <br><br>This is to notify you that your wallet balance is low on coin" \
              f"<br>New wallet balance: <strong>{amount} coins</strong>"\
              f"<br>Please login to your dashboard and fund your wallet"
    subject = "Low Balance"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def payout_request_email(user, lang):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Tutor"

    message = f"Dear {name}, <br><br>Your payout request has been created and will be proccessed in seven (7) days" \
              f"<br>The fund will reflect in select account."
    subject = "Payout Request"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def parent_intro_call_email(user, tutor_name, start_date, end_date, link, lang):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Parent"

    message = f"Dear {name}, <br><br>Your Virtual Intro Call with tutor {tutor_name} on EduDream has been scheduled." \
              f"<br>Start: <strong>{start_date}</strong>" \
              f"<br>End: <strong>{end_date}</strong>" \
              f"<br>Meeting Link: <strong>{link}</strong>"
    subject = f"EduDream: Intro Call with {tutor_name}"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def tutor_intro_call_email(user, u_name, start_date, end_date, link, lang):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Tutor"

    message = f"Dear {name}, <br><br>You have a Virtual Intro Call request from {u_name} on EduDream." \
              f"<br>Start: <strong>{start_date}</strong>" \
              f"<br>End: <strong>{end_date}</strong>" \
              f"<br>Meeting Link: <strong>{link}</strong>"
    subject = f"EduDream: Intro Call with {u_name}"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def feedback_email(email, f_name, f_email, msg, lang):
    name = "EduDream Admin"
    message = f"Dear {name}, <br><br>You have received a new feedback from {f_name} on EduDream." \
              f"<br>Email: <strong>{f_email}</strong>" \
              f"<br>Message: <strong>{msg}</strong>"
    subject = f"EduDream: New Feedback"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def consultation_email(email, f_name, f_email, acct_type, lang):
    name = "EduDream Admin"
    message = f"Dear {name}, <br><br>You have received a new consultation request from {f_name} on EduDream." \
              f"<br>Email: <strong>{f_email}</strong>" \
              f"<br>Account Type: <strong>{acct_type}</strong>"
    subject = f"EduDream: New Consultation Request"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def send_otp_token_to_email(user_profile, otp, lang):
    email = user_profile.user.email
    message = f"Hello, <br><br>Kindly use the below One Time Token, to complete your action<br><br>" \
              f"OTP: <strong>{otp}</strong>"
    subject = "EduDream: One-Time-Passcode"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def send_token_to_email(user_profile):
    first_name = user_profile.user.first_name
    if not user_profile.user.first_name:
        first_name = "EduDream User"
    email = user_profile.user.email
    decrypted_token = decrypt_text(user_profile.otp)

    message = f"Dear {first_name}, <br><br>Kindly use the below One Time Token, to complete your action<br><br>" \
              f"OTP: <strong>{decrypted_token}</strong>"
    subject = "EduDream Verification"
    translated_content = translate_email(message, "fr")
    translated_subject = translate_email(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def send_verification_email(user_profile, lang):
    site_setting = get_site_details()
    frontend_base_url = site_setting.frontend_url

    first_name = user_profile.user.first_name
    if not user_profile.user.first_name:
        first_name = "EduDream User"
    email = user_profile.user.email

    message = f"Dear {first_name}, <br><br>Kindly click <a href='{frontend_base_url}/#/auth/sign-in?token={user_profile.email_verified_code}' target='_blank'>here</a> to verify your email. "
    subject = f"EduDream Email Verification"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def send_welcome_email(user_profile, lang):
    first_name = user_profile.user.first_name
    if not user_profile.user.first_name:
        first_name = "EduDream User"
    email = user_profile.user.email

    message = f'<p class="letter-heading">Hello <span>{first_name}!</span> <br><br><br><br></p>' \
              f'<div class="letter-body"><p>Welcome to EduDream.<br>' \
              f'<br>Our mission is to revolutionize online education by providing personalized, accessible, and ' \
              f'affordable tutoring to foster academic excellence and personal growth in every student.<br><br>'

    subject = f"Welcome to EduDream"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def send_class_reminder_email(user, classroom, minu, lang):
    first_name = user.first_name
    if not user.first_name:
        first_name = "EduDream User"
    email = user.email

    message = f"Dear {first_name}, <br><br>A classroom will start in the next {minu} minute(s)" \
              f"<br>Class Name: <strong>{classroom.name}</strong>" \
              f"<br>Tutor Name: <strong>{classroom.tutor.get_full_name()}</strong>"
    if minu == 0:
        message = f"Dear {first_name}, <br><br>A classroom {classroom.name} with {classroom.tutor.get_full_name()} " \
                  f"is starting now." \

    subject = f"Class Reminder"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def send_class_ended_reminder_email(email, classroom, lang):
    message = f"Hello!, <br><br>A classroom has just ended. Please login to your dashboard to mark it as completed " \
              f"<br>Class Name: <strong>{classroom.name}</strong>" \
              f"<br>Tutor Name: <strong>{classroom.tutor.get_full_name()}</strong>" \
              f"<br>Kindly ignore this email, you have already marked this class as completed"

    subject = f"Class Ended"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def send_fund_pending_balance_email(user, classroom, lang):
    first_name = user.first_name
    if not user.first_name:
        first_name = "EduDream Tutor"
    email = user.email

    message = f"Dear {first_name}, <br><br>Congratulations! Your fund for completed class is now pending, " \
              f"and will reflect in your main balance after 7 days" \
              f"<br>Class Name: <strong>{classroom.name}</strong>" \

    subject = f"Fund on the way"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def send_fund_main_balance_email(user, classroom, lang):
    first_name = user.first_name
    if not user.first_name:
        first_name = "EduDream Tutor"
    email = user.email

    message = f"Dear {first_name}, <br><br>Congratulations! Your fund for completed class is now moved to " \
              f"your main balance, " \
              f"<br>Class Name: <strong>{classroom.name}</strong>" \

    subject = f"Payment to wallet"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def auto_classroom_complete_email(user, classroom, lang="en"):
    first_name = user.first_name
    if not user.first_name:
        first_name = "EduDream Tutor"
    email = user.email

    message = f"Dear {first_name}, <br><br>A recent class you taught is now marked as <strong>COMPLETED</strong>. " \
              f"Your payment will reflect in your wallet balance shortly." \
              f"<br>Class Name: <strong>{classroom.name}</strong>" \

    subject = f"Class Completed"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def send_payout_processed_email(user, amount, lang):
    first_name = user.first_name
    if not user.first_name:
        first_name = "EduDream Tutor"
    email = user.email

    message = f"Dear {first_name}, <br><br>Your payout request is processed, and fund will be credited to your " \
              f"shortly. " \
              f"<br>Payout Amount: <strong>{amount}</strong>" \

    subject = f"Payout Processed"
    translated_content = translate_email(message, lang)
    translated_subject = translate_email(subject, lang)
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


