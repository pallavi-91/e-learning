from django.db import models

class SupportedGateway(models.TextChoices):
    PAYPAL = 'Paypal'
    HYPERPAY = 'HyperPay'

class PaymentMethods(models.TextChoices):
    BANK_TRANSFER = 'Direct To Bank'
    ONLINE_TRANSFER = 'Online Transfer'
    CARD = 'Card'

class ShareTypes(models.TextChoices):
    ORGANICS = 'ORGANICS', 'Organics'
    ADS = 'ADS', 'Ads'
    INSTRUCTOR_REFERRAL = 'INSTRUCTOR_REFERRAL', 'Instructor Referral'
    AFFILIATE = 'AFFILIATE', 'Affiliate'
    STUDENT_REFERRAL = 'STUDENT_REFERRAL', 'Student Referral'

class InstructorGroups(models.TextChoices):
    DEFAULT = 'default', 'Instructor (Default)'
    PREMIUM_INSTRUCTOR = 'premium', 'Premium Instructor'
    PARTNET_INSTRUCTOR = 'partner', 'Partner Instructor'
    
class RefundStatus(models.TextChoices):
    REFUND_PENDING = 'Pending'
    REFUND_APPROVED = 'Approved'
    REFUND_SUCCESS = 'Refunded'
    REFUND_REJECTED = 'Rejected'
    REFUND_CANCELED = 'Cancelled'
    REFUND_CHARGEBACK = 'Chargeback'
    REFUND_RECONCILE = 'Reconciliation'
    
class TransactionTypes(models.TextChoices):
    SALE = 'Sale'
    PAYOUT = 'Payout'
    REFUND = 'Refund'
    
class StatementEventTypes(models.TextChoices):
    EARNINGS = 'Earnings'
    CHARGEBACK = 'Chargeback'
    REFUND = 'Refund'
    RECONCILATION = 'Reconcilation'

class TransactionStatus(models.TextChoices):
    AVAILABLE = 'Available'
    PENDING = 'Pending'
    DENIED = 'Denied'
    PROCESSING = 'Processing'
    SUCCESS = 'Success'
    CANCELED = 'Canceled'
    FAILED = 'Failed'
    
class PayoutStatus(models.TextChoices):
    # Funds have been credited to the recipient’s account.
    SUCCESS = 'Success'
    # This payout request has failed, so funds were not
    # deducted from the sender’s account.
    FAILED = 'Failed'
    # Your payout request was received and will be processed (in review).
    PENDING = 'Pending'
    # The recipient for this payout does not have a PayPal account.
    # A link to sign up for a PayPal account was sent to the recipient.
    # However, if the recipient does not claim this payout within 30 days,
    # the funds are returned to your account.
    UNCLAIMED = 'Unclaimed'
    # The recipient has not claimed this payout, so the funds have been
    # returned to your account.
    RETURNED = 'Returned'
    # This payout request is being reviewed and is on hold.
    ONHOLD = 'On-hold'
    # This payout request has been blocked.
    BLOCKED = 'Blocked'
    # This payout request was refunded.
    REFUNDED = 'Refunded'
    # This payout request was reversed.
    REVERSED = 'Reversed'
    # This payout request is reviewed and marked Read.
    READY = 'Ready'
    

class PayoutType(models.TextChoices):
    UPCOMING = 'Upcoming'
    ONGOING = 'OnGoing'
    PAID = 'Paid'
    FAILED = 'Failed'
    INACTIVE = 'Inactive'# Payout will in Inactive if instructor account is inactive or if instructor payout_pay_status is False

class HoldTransactionStatus(models.TextChoices):
    HOLD = 'Hold'
    UNHOLD = 'UnHold'

class PayoutTransitionStatus(models.TextChoices):
    MARK_AS_PAID = 'Mark As Paid'
    INACTIVE_PAID = 'Inactive Paid'
     
class RefundType(models.TextChoices):
    REGULAR = 'Regular Refund'
    THKEE = 'Thkee Refund'
    
class OrderStatus(models.TextChoices):
    CREATED = "Created"
    SAVED = "Saved"
    APPROVED = "Approved"
    VOIDED = "Voided"
    COMPLETED = "Completed"
    PAYER_ACTION_REQUIRED = "Payer Action Required"

class PayoutPayStatus(models.TextChoices):
    PARTIAL = 'Partially Paid'
    FULL = 'Full Paid'
    UNPAID = 'UnPaid'
    BLANK = 'N/A'


class CourseStatus(models.TextChoices):
    STATUS_DRAFT ="Draft"
    STATUS_PUBLISHED ="Published"
    STATUS_REJECTED ="Rejected"
    STATUS_INREVIEW ="In Review"
    STATUS_UNLISTED ="UnListed"

class CourseResourceMode(models.TextChoices):
    VIDEO_BASED ="Video Based"
    ARTICLE_BASED ="Article Based"
    SINGLE_SESSION ="Single Session"
    MULTIPLE_SESSION ="Multple Session"
    HYBRID ="Hybrid"

class CourseLectureType(models.TextChoices):
    VIDEO ="Video"
    ARTICLE ="Article"

class CourseSkillLevel(models.TextChoices):
    SKILL_BEGINNER = 'Beginner'
    SKILL_INTERMEDIATE = 'Intermediate'
    SKILL_EXPERT = 'Expert'
    SKILL_ALL = 'All'

class CourseType(models.TextChoices):
    PAID = 'Paid'
    FREE = 'Free'
    
class StatementStatus(models.TextChoices):
    OPEN = 'Open'
    CLOSED = 'Closed'
    CURRENT = 'Current'

class NotesType(models.TextChoices):
    NOTE = 'Note'
    HIGHLIGHT = 'Highlight'


class NotificationType(models.TextChoices):
    ANNOUNCEMENTS = 'ANNOUNCEMENTS'
    NOTES = 'NOTES'
    REVIEWS = 'REVIEWS'


class FieldCourseInReview(models.TextChoices):
    TITLE = 'title'
    SUBTITLE = 'subtitle'
    DETAIL = 'desc'
    IMAGE = 'image'
    PROMO_VIDEO = 'promo_video'
    TOPICS = 'topics'
    DESCRIPTION = 'description'
    SKILL_LEVEL = 'skill_level'
    CATEGORY = 'category'
    SUBCATEGORY = 'subcategory'
    LANGUAGE = 'language'
    OBJECTIVES = 'objectives' 
    REQUIREMENTS = 'requirements' 
    LEARNINGS = 'learners' 
    VIDEO_THUMBNAIL = 'video_info'
    SECTION = 'section'
    QUIZ = 'quiz'
    ASSIGNMENT = 'assignment'
    LECTURE = 'lecture'
    QUIZ_QUESTION = 'quiz_question'
    ASSIGNMENT_QUESTION = 'assignment_question'
    PRICING = 'pricing'