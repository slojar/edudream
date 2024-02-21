from django.shortcuts import render
from edudream.modules.utils import send_email, translate_to_language


def parent_class_creation_email(classroom):
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
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def tutor_class_creation_email(classroom):
    email = classroom.tutor.email
    student_name = str(classroom.student.get_full_name()).upper()
    tutor_name = classroom.tutor.first_name
    if not tutor_name:
        tutor_name = "EduDream Tutor"

    message = f"Dear {tutor_name}, <br><br>You have a new classroom request from <strong>{student_name}</strong>" \
              f"<br>Kindly login to your dashboard to accept or decline the request."
    subject = "New Class Room Request"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def tutor_class_approved_email(classroom):
    email = classroom.tutor.email
    class_name = classroom.name
    link = classroom.meeting_link
    amount = classroom.amount
    student_name = str(classroom.student.get_full_name()).upper()
    tutor_name = classroom.tutor.first_name
    if not tutor_name:
        tutor_name = "EduDream Tutor"

    message = f"Dear {tutor_name}, <br><br>You have accepted to take the following class with " \
              f"<strong>{student_name}</strong><br>Class Name: <strong>{class_name}</strong><br>Class Link: " \
              f"<strong>{link}</strong><br>Class Fee: <strong>{amount}</strong>"
    subject = "Classroom Request Approved"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def student_class_approved_email(classroom):
    email = classroom.student.user.email
    class_name = classroom.name
    link = classroom.meeting_link
    student_name = str(classroom.student.first_name())
    tutor_name = classroom.tutor.get_full_name()
    if not student_name:
        student_name = "EduDream Student"

    message = f"Dear {student_name}, <br><br>Your request to start the following class was approved by your tutor" \
              f"<br>Class Name: <strong>{class_name}</strong><br>Class Link: " \
              f"<strong>{link}</strong><br>Tutor Name: <strong>{tutor_name}</strong>"
    subject = "Classroom Request Approved"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def student_class_declined_email(classroom):
    email = classroom.student.user.email
    class_name = classroom.name
    reason = classroom.decline_reason
    student_name = str(classroom.student.first_name())
    if not student_name:
        student_name = "EduDream Student"

    message = f"Dear {student_name}, <br><br>Your request to start the following class was declined by the tutor" \
              f"<br>Class Name: <strong>{class_name}</strong>" \
              f"<br>Status: <strong>DECLINED</strong>" \
              f"<br>Decline Reason: <strong>{reason}</strong>"
    subject = "Classroom Request Declined!"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def tutor_register_email(user):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Tutor"

    message = f"Dear {name}, <br><br>You have successfully registered on Edudream as a Tutor" \
              f"<br>Your account is under review, and will be active shortly."
    subject = "Signup Successful"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
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
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def parent_register_email(user):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Parent"

    message = f"Dear {name}, <br><br>You have successfully registered on Edudream as a Parent" \
              f"<br>Please login to your dashboard to add your child/ward"
    subject = "Signup Successful"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def parent_class_cancel_email(user, amount):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Parent"

    message = f"Dear {name}, <br><br>A classroom was cancelled and {amount} coins have been refunded to your wallet" \
              f"<br>Please login to your dashboard to confirm"
    subject = "Cancelled Class"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def student_class_cancel_email(user, classroom):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Student"

    message = f"Dear {name}, <br><br>A classroom was cancelled by your tutor" \
              f"<br>Class Name: <strong>{classroom.name}</strong>" \
              f"<br>Tutor Name: <strong>{classroom.tutor.get_full_name()}</strong>"
    subject = "Cancelled Class"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def parent_low_threshold_email(user, amount):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Parent"

    message = f"Dear {name}, <br><br>This is to notify you that your wallet balance is low on coin" \
              f"<br>New wallet balance: <strong>{amount} coins</strong>"\
              f"<br>Please login to your dashboard and fund your wallet"
    subject = "Low Balance"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def payout_request_email(user):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Tutor"

    message = f"Dear {name}, <br><br>Your payout request has been created and will be proccessed in seven (7) days" \
              f"<br>The fund will reflect in select account."
    subject = "Payout Request"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def parent_intro_call_email(user, tutor_name, start_date, end_date, link):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Parent"

    message = f"Dear {name}, <br><br>Your Virtual Intro Call with tutor {tutor_name} on EduDream has been scheduled." \
              f"<br>Start: <strong>{start_date}</strong>" \
              f"<br>End: <strong>{end_date}</strong>" \
              f"<br>Meeting Link: <strong>{link}</strong>"
    subject = f"EduDream: Intro Call with {tutor_name}"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def tutor_intro_call_email(user, u_name, start_date, end_date, link):
    email = user.email
    name = user.first_name
    if not name:
        name = "EduDream Tutor"

    message = f"Dear {name}, <br><br>You have a Virtual Intro Call request from {u_name} on EduDream." \
              f"<br>Start: <strong>{start_date}</strong>" \
              f"<br>End: <strong>{end_date}</strong>" \
              f"<br>Meeting Link: <strong>{link}</strong>"
    subject = f"EduDream: Intro Call with {u_name}"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def feedback_email(email, f_name, f_email, msg):
    name = "EduDream Admin"
    message = f"Dear {name}, <br><br>You have received a new feedback from {f_name} on EduDream." \
              f"<br>Email: <strong>{f_email}</strong>" \
              f"<br>Message: <strong>{msg}</strong>"
    subject = f"EduDream: New Feedback"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def consultation_email(email, f_name, f_email, acct_type):
    name = "EduDream Admin"
    message = f"Dear {name}, <br><br>You have received a new consultation request from {f_name} on EduDream." \
              f"<br>Email: <strong>{f_email}</strong>" \
              f"<br>Account Type: <strong>{acct_type}</strong>"
    subject = f"EduDream: New Consultation Request"
    translated_content = translate_to_language(message, "fr")
    translated_subject = translate_to_language(subject, "fr")
    contents = render(None, 'default_template.html', context={'message': translated_content}).content.decode('utf-8')
    send_email(contents, email, translated_subject)
    return True


def send_otp_token_to_email(user_profile, otp):
    email = user_profile.user.email
    message = f"Hello, <br><br>Kindly use the below One Time Token, to complete your action<br><br>" \
              f"OTP: <strong>{otp}</strong>"
    subject = "EduDream: One-Time-Passcode"
    contents = render(None, 'default_template.html', context={'message': message}).content.decode('utf-8')
    send_email(contents, email, subject)
    return True



