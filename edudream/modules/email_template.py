from django.shortcuts import render
from edudream.modules.utils import send_email


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
    contents = render(None, 'default_template.html', context={'message': message}).content.decode('utf-8')
    send_email(contents, email, subject)
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
    contents = render(None, 'default_template.html', context={'message': message}).content.decode('utf-8')
    send_email(contents, email, subject)
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
    contents = render(None, 'default_template.html', context={'message': message}).content.decode('utf-8')
    send_email(contents, email, subject)
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
    contents = render(None, 'default_template.html', context={'message': message}).content.decode('utf-8')
    send_email(contents, email, subject)
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
    contents = render(None, 'default_template.html', context={'message': message}).content.decode('utf-8')
    send_email(contents, email, subject)
    return True





