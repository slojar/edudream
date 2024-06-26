TRANSACTION_TYPE_CHOICES = (
    ("fund_wallet", "Fund Wallet"), ("course_payment", "Course Payment"), ("withdrawal", "Withdrawal"),
    ("refund", "Refund"), ("bonus", "Bonus")
)

PAYMENT_METHOD_CHOICES = (
    ("card", "Card"), ("bank_transfer", "Bank Transfer"), ("wallet", "Wallet")
)

TRANSACTION_STATUS_CHOICES = (
    ("completed", "Completed"), ("pending", "Pending"), ("failed", "Failed")
)

ACCOUNT_TYPE_CHOICES = (
    ("tutor", "Tutor"), ("parent", "Parent")
)

ACCEPT_DECLINE_STATUS = (
    ("accept", "Accept"), ("decline", "Decline"), ("cancel", "Cancel")
)

DISPUTE_TYPE_CHOICES = (
    ("payment", "Payment"), ("student", "Student"), ("others", "Others")
)

DISPUTE_STATUS_CHOICES = (
    ("open", "Open"), ("resolved", "Resolved")
)

CLASS_STATUS_CHOICES = (
    ("new", "New"), ("accepted", "Accepted"), ("declined", "Declined"), ("completed", "Completed"),
    ("cancelled", "Cancelled")
)

CLASS_TYPE_CHOICES = (
    ("normal", "Normal"), ("custom", "Custom")
)

AVAILABILITY_STATUS_CHOICES = (
    ("available", "Available"), ("not_available", "Not Available")
)

DAY_OF_THE_WEEK_CHOICES = (
    ("0", "Sunday"), ("1", "Monday"), ("2", "Tuesday"), ("3", "Wednesday"), ("4", "Thursday"), ("5", "Friday"),
    ("6", "Saturday")
)

PROFICIENCY_TYPE_CHOICES = (
    ("professional", " Professional"), ("conversational", "Conversational"), ("learning", "Learning"),
    ("native", "Native")
)

PAYOUT_STATUS_CHOICES = (
    ("pending", "Pending"), ("processed", "Processed")
)

GRADE_CHOICES = (
    ("mid_school", "Middle School"), ("high_school", "High School")
)

SEND_NOTIFICATION_TYPE_CHOICES = (
    ("tutor", "Tutor"), ("parent", "Parent"), ("student", "Student"), ("all", "All")
)

APPROVE_OR_DECLINE_CHOICES = (
    ("approved", "Approve"), ("declined", "Decline")
)

CONSULTATION_TYPE_CHOICES = (
    ("consult", "Consultation"), ("feedback", "Feedback")
)

CONSULTATION_ACCOUNT_TYPE = (
    ("parent", "Parent"), ("student", "Student"), ("tutor", "Tutor")
)

TUTOR_STATUS_CHOICES = (
    ("pending", "Pending"), ("approved", "Approved"), ("declined", "Declined")
)

ADD_SUBTRACT_ACTION_CHOICES = (
    ("add", "Addition"), ("subtract", "Subtraction")
)
