TRANSACTION_TYPE_CHOICES = (
    ("fund_wallet", "Fund Wallet"), ("course_payment", "Course Payment"), ("withdrawal", "Withdrawal")
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
    ("accept", "Accept"), ("decline", "Decline")
)

DISPUTE_TYPE_CHOICES = (
    ("payment", "Payment"), ("student", "Student"), ("others", "Others")
)

DISPUTE_STATUS_CHOICES = (
    ("open", "Open"), ("resolved", "Resolved")
)

