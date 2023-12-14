from django.db.utils import OperationalError
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from django.db import connections
from apps.countries.models import Country
from apps.shares.models import ChannelModelSerializer, InstructorGroups, SharePrices, ShareTypes
from apps.transactions.models import PaymentMethods, SupportedGateway, TransactionStatus, TransactionTypes, Transactions, PaymentType
from apps.transactions.tasks import setup_instructor_ongoing_payouts, setup_instructor_upcoming_payouts, all_statements, update_statements
from apps.users.models import Instructor, UserClass, Order, User as ThkeeUser
from apps.courses.models import Assignment, Course, CoursePrice, Category, Lecture, Quiz, QuizAnswer, QuizQuestion, SubCategory, Section, SubSection, Topic
from apps.currency.models import Currency

try:
    from django.db.models import loading
except ImportError:
    from django.apps import apps as loading
from django.db import close_old_connections
from faker import Faker
fake = Faker()


class Command(BaseCommand):
    args = '<[--fakeEntry | -fe] [--dbName | -db] [--dropDb | -d]>'
    help = """
           Generate fixtures
           for a given object, generate json fixtures to rediret
           to a file in order to have full hierarchy of models
           from this parent object.
           syntax example:
               python manage.py generate_seed --fakeEntry=10 --dbName=test
           """
    ENTRY = 10
    def add_arguments(self, parser):
        """Add command line arguments to parser"""
        super().add_arguments(parser)
        # Required Args
        parser.add_argument('--dbName', '-db',
                            dest='dbName',
                            default='default',
                            help='Use database on which fake entry need to created.')

        parser.add_argument('--fakeEntry', '-fe',
                            dest='fakeEntry',
                            type=int,
                            default=50,
                            help='Attempts to get n number of fake entries.')

        parser.add_argument('--dropDb', '-d',
                            action='store_const',
                            dest='dropDb',
                            const=True,
                            help='Drop all the existing entry')

    def getInstructorUser(self):
        self.stdout.write('Generating fake data for instructor')
        instructors = Instructor.objects.order_by('?')
        payments = PaymentType.objects.all()
        if not instructors.exists():
            instructors_list = []
            for _ in range(self.ENTRY):
                try:
                    # Add new Instructors
                    payout_method = fake.random_element(payments)
                    data = {
                        'email': fake.unique.email(),
                        'first_name': fake.first_name_male(),
                        'last_name':  fake.last_name(),
                        'is_active': True,
                    }
                    user = ThkeeUser.objects.create(**data)
                    instructors_list.append(Instructor(user=user, payout_method=payout_method))
                except Exception as ex:
                    print(ex)
            instructors = Instructor.objects.bulk_create(instructors_list, ignore_conflicts=True)
            for user in instructors:
                try:
                    user.save()
                except IntegrityError:
                    pass
                
        instructors_users = ThkeeUser.objects.exclude(instructor=None)
        return instructors_users
    
    def getStudentUser(self, *args, **kwargs):
        self.stdout.write('Generating fake data for student user')
        users = ThkeeUser.objects.filter(instructor=None, is_superuser=False)
        if not users.exists():
            user_set = []
            for _ in range(self.ENTRY):
                data = {
                    'email': fake.unique.email(),
                    'first_name': fake.first_name_male(),
                    'last_name':  fake.last_name(),
                    'is_active': True,
                }
                user_set.append(ThkeeUser(**data))
            users = ThkeeUser.objects.bulk_create(user_set, ignore_conflicts=True)
            for user in users:
                try:
                    user.save()
                except IntegrityError:
                    pass
            users = ThkeeUser.objects.filter(instructor=None)
        return users
    
    def getCurrency(self):
        self.stdout.write('Generating fake data for currency')
        currencies = Currency.objects.order_by('?')
        if not currencies.exists():
            currency_set = []
            countries = self.getCountry()
            for _ in range(self.ENTRY):
                currency_code, currency_name = fake.currency()
                
                data = {
                    "name": currency_name,
                    "currency_code": currency_code,
                    "rate": fake.random.randint(1,50)
                }
                currency_set.append(Currency(**data))
            currencies = Currency.objects.bulk_create(currency_set, ignore_conflicts=True)
            for currency in currencies:
                try:
                    currency.save()
                    country = fake.random_elements(countries)
                    currency.country.add(*country)
                    currency.save()
                except IntegrityError:
                    pass
            currencies = Currency.objects.order_by('?')
        return currencies
    
    def getCountry(self):
        self.stdout.write('Generating fake data for country')
        countries = Country.objects.order_by('?')
        if not countries.exists():
            country_set = []
            for _ in range(self.ENTRY):
                data = {
                    "name": fake.country(),
                    "two_letter_iso_code": fake.country_code(),
                    "three_letter_iso_code": fake.country_code(representation='alpha-3'),
                    "numeric_iso_code": fake.random.randint(10,500),
                }
                country_set.append(Country(**data))
            countries = Country.objects.bulk_create(country_set, ignore_conflicts=True)
            
        return countries
    
    def getCoursePrice(self):
        self.stdout.write('Generating fake data for course price')
        prices = CoursePrice.objects.order_by('?')
        if not prices.exists():
            prices_set = []
            currency_list = self.getCurrency()
            for nm in range(self.ENTRY):
                currency = fake.random_element(currency_list)
                data = {
                    'price': fake.random.randint(100,500),
                    'name': fake.first_name_male(),
                    'currency': currency,
                    'price_tier_status': True,
                    'tier_level': nm,
                }
                prices_set.append(CoursePrice(**data))
            prices = CoursePrice.objects.bulk_create(prices_set, ignore_conflicts=True)
            for item in prices:
                try:
                    item.save()
                except IntegrityError:
                    pass
            prices = CoursePrice.objects.order_by('?')
        return prices
    
    
    def getTopics(self):
        self.stdout.write('Generating fake data for topics')
        items = Topic.objects.order_by('?')
        if not items.exists():
            items_set = []
            for _ in range(self.ENTRY):
                data = {
                    'name': fake.unique.word()
                }
                items_set.append(Topic(**data))
            items = Topic.objects.bulk_create(items_set, ignore_conflicts=True)
            for item in items:
                try:
                    item.save()
                except IntegrityError:
                    pass
            items = Topic.objects.order_by('?')
        return items
    
    def getCategory(self):
        self.stdout.write('Generating fake data for category')
        items = Category.objects.order_by('?')
        if not items.exists():
            items_set = []
            for _ in range(self.ENTRY):
                data = {
                    'name': fake.bs()
                }
                items_set.append(Category(**data))
            items = Category.objects.bulk_create(items_set, ignore_conflicts=True)
            for item in items:
                try:
                    item.save()
                except IntegrityError:
                    pass
            items = Category.objects.order_by('?')
        return items
    
    def getSubCategory(self):
        self.stdout.write('Generating fake data for sub category')
        items = SubCategory.objects.order_by('?')
        if not items.exists():
            items_set = []
            category_list = self.getCategory()
            for _ in range(self.ENTRY):
                category = fake.random_element(category_list)
                data = {
                    'category': category,
                    'name': fake.job()
                }
                items_set.append(SubCategory(**data))
            items = SubCategory.objects.bulk_create(items_set, ignore_conflicts=True)
            for item in items:
                try:
                    item.save()
                except IntegrityError:
                    pass
            items = SubCategory.objects.order_by('?')
        return items
    
    def fakeCourses(self, *args, **kwargs):
        self.stdout.write('Generating fake data for course')
        items_set = []
        subcategory_list = self.getSubCategory()
        pricing_list = self.getCoursePrice()
        instructor_user = self.getInstructorUser()
        for _ in range(self.ENTRY):
            pricing = fake.random_element(pricing_list)
            user = fake.random_element(instructor_user)
            subcategory = fake.random_element(subcategory_list)
            data = {
                'user': user,
                'pricing': pricing,
                'price': pricing.price,
                'title': fake.job(),
                'subtitle': fake.sentence(),
                'desc': fake.text(),
                'category': subcategory.category,
                'subcategory': subcategory,
            }
            
            items_set.append(Course(**data))
            
        courses = Course.objects.bulk_create(items_set, ignore_conflicts=True)
        topics = self.getTopics()
        for course in courses:
            try:
                course.save()
                topics = fake.random_elements(topics)
                course.topics.add(*topics)
                # Add sections for each course
                self.fakeSection(course)
            except IntegrityError:
                pass

    def fakeSection(self, course):
        self.stdout.write('Generating fake data for section')
        section_list = []
        for _ in range(self.ENTRY):
            data = {
                'title': fake.word(),
                'course': course
            }
            section_list.append(Section(**data))
        sections = Section.objects.bulk_create(section_list, ignore_conflicts=True)
        for section in sections:
            # Add lectures
            section.save()
            lecture = self.fakeLecture(section)
            quizes = self.fakeQuiz(section, lecture)
            assignments = self.fakeAssignment(section, lecture)
            assignment = fake.random_element(assignments)
            quiz = fake.random_element(quizes)
            self.fakeSubSection(section=section, lecture=lecture, quiz=quiz, assignment=assignment)
    
    def fakeLecture(self, section):
        self.stdout.write('Generating fake data for lecture')
        lecture_list = []
        for _ in range(self.ENTRY):
            data = {
                'title': fake.word(),
                'section': section
            }
            lecture_list.append(Lecture(**data))
        lectures = Lecture.objects.bulk_create(lecture_list, ignore_conflicts=True)
        for item in lectures:
            item.save()
        return fake.random_element(lectures)
    
    def fakeQuiz(self, section, lecture):
        self.stdout.write('Generating fake data for quiz')
        items_list = []
        for _ in range(self.ENTRY):
            data = {
                'title': fake.word(),
                'section': section
            }
            items_list.append(Quiz(**data))
        quizes = Quiz.objects.bulk_create(items_list, ignore_conflicts=True)
        for quiz in quizes:
            quiz.save()
            self.fakeQuizQuestion(lecture, quiz)
        return quizes
    
    def fakeQuizQuestion(self, lecture, quiz):
        self.stdout.write('Generating fake data for quiz question')
        items_list = []
        for _ in range(self.ENTRY):
            data = {
                'question': fake.text(),
                'lecture': lecture,
                'quiz': quiz
            }
            items_list.append(QuizQuestion(**data))
        questions = QuizQuestion.objects.bulk_create(items_list, ignore_conflicts=True)
        self.stdout.write('Generating fake data for quiz answer')
        for question in questions:
            question.save()
            self.fakeQuizAnswer(question)
        
    
    def fakeQuizAnswer(self, quiz_question):
        items_list = []
        for _ in range(5):
            data = {
                'answer': fake.text(),
                'quiz_question': quiz_question,
                'expected': fake.text()
            }
            items_list.append(QuizAnswer(**data))
        QuizAnswer.objects.bulk_create(items_list, ignore_conflicts=True)
    
    def fakeAssignment(self, section, lecture):
        self.stdout.write('Generating fake data for assignment')
        items_list = []
        for _ in range(self.ENTRY):
            data = {
                'title': fake.text(),
                'lecture': lecture,
                'section': section
            }
            items_list.append(Assignment(**data))
        assignments = Assignment.objects.bulk_create(items_list, ignore_conflicts=True)
        for assignment in assignments:
            assignment.save()
        return assignments
    
    def fakeSubSection(self, section, quiz, lecture, assignment):
        self.stdout.write('Generating fake data for sub section')
        items_list = []
        for _ in range(self.ENTRY):
            data = {
                'section': section,
                'quiz': quiz,
                'lecture': lecture,
                'assignment': assignment,
            }
            items_list.append(SubSection(**data))
        sub_sections = SubSection.objects.bulk_create(items_list, ignore_conflicts=True)
        for sub_section in sub_sections:
            sub_section.save()
            
        return sub_sections
    
    # Student Orders
    def fakeOrders(self):
        self.stdout.write('Generating fake data for student orders')
        items_list = []
        students = ThkeeUser.objects.filter(instructor=None, is_superuser=False)
        shares = SharePrices.objects.order_by('?')
        for _ in range(self.ENTRY):
            channel = fake.random_element(shares)
            data = {
                'user': fake.random_element(students),
                'channel': ChannelModelSerializer(channel).data,
            }
            items_list.append(Order(**data))
        orders = Order.objects.bulk_create(items_list, ignore_conflicts=True)
        for order in orders:
            try:
                courses = Course.objects.order_by('?')[:5]
                order.save()
                order.add_courses(courses)
            except Exception as ex:
                print(ex)
        return orders
    
    # Student Class Fake
    def fakeClasses(self, *args, **kwargs):
        self.stdout.write('Generating fake data for student class')
        items_list = []
        
        courses = Course.objects.order_by('?')
        subsections = SubSection.objects.order_by('?')
        currency = Currency.objects.order_by('?')
        orders = Order.objects.order_by('?')
        
        for _ in range(self.ENTRY):
            order = fake.random_element(orders)
            course = fake.random_element(courses)
            data = {
                'user': order.user,
                'course': course,
                'currency': fake.random_element(currency),
                'price': course.price,
                'order': order,
            }
            items_list.append(UserClass(**data))
        classes = UserClass.objects.bulk_create(items_list, ignore_conflicts=True)
        for order in classes:
            order.save()
            subsection = fake.random_elements(subsections)
            order.subsections.add(*subsection)
            
        return classes
    
    # Payment type Fake
    def fakePaymentType(self, *args, **kwargs):
        self.stdout.write('Generating fake data for Payment Type')
        items_list = []
        count = 0
        for _, ptype in PaymentMethods.choices:
            data = {
                'payment_gateway': SupportedGateway.choices[0][0],
                'payment_method': ptype,
                'gateway_charge': 2
            }
            items_list.append(PaymentType(**data))
            count+=1
        PaymentType.objects.bulk_create(items_list, ignore_conflicts=True)
    
    def fakeTransactions(self, *args, **kwargs):
        self.stdout.write('Generating fake data for Transactions')
        items_list = []
        user_classes = UserClass.objects.order_by('?')
        payments = PaymentType.objects.all()
        for _ in range(self.ENTRY):
            user_class = fake.random_element(user_classes)
            payment_type = fake.random_element(payments)
            status = TransactionStatus.SUCCESS
            data = {
                'student': user_class.user,
                'instructor': user_class.course.user,
                'order': user_class.order,
                'type': TransactionTypes.SALE ,
                'status': status,
                'gross_amount': user_class.price,
                'currency': user_class.currency,
                'channel': user_class.order.channel,
                'user_class': user_class,
                'payment_type': payment_type,
                'gateway_charge': 2
            }
            items_list.append(Transactions(**data))
                
        transactions = Transactions.objects.bulk_create(items_list, ignore_conflicts=True)
        for order in transactions:
            order.save()
        # Update statemenst
        all_statements()
        update_statements()
        setup_instructor_ongoing_payouts()
        setup_instructor_upcoming_payouts()
        return transactions
    
    def fakeSharePrices(self, *args, **kwargs):
        self.stdout.write('Generating fake data for channel (SharePrices)')
        items_list = []
        
        choices = [ShareTypes.ORGANICS, ShareTypes.INSTRUCTOR_REFERRAL, ShareTypes.AFFILIATE, ShareTypes.ADS, ShareTypes.STUDENT_REFERRAL]
        for share_type in choices:
            if share_type in [ShareTypes.ORGANICS, ShareTypes.INSTRUCTOR_REFERRAL, ShareTypes.ADS]:
                for group_name, _ in InstructorGroups.choices:
                    data = {
                        'share_types': share_type,
                        'instructor_share': 20,
                        'platform_share': 80,
                        'affiliate_share': 0,
                        'thkee_credit': 0,
                        'group_name': group_name
                    }
                    items_list.append(SharePrices(**data))
                    
            elif share_type in ShareTypes.AFFILIATE:
                for group_name, _ in InstructorGroups.choices:
                    data = {
                        'share_types': share_type,
                        'instructor_share': 10,
                        'platform_share': 80,
                        'affiliate_share': 10,
                        'thkee_credit': 0,
                        'group_name': group_name
                    }
                    items_list.append(SharePrices(**data))
            else:
                data = {
                        'share_types': share_type,
                        'instructor_share': 10,
                        'platform_share': 80,
                        'affiliate_share': 0,
                        'thkee_credit': 10,
                        'group_name': ''
                    }
                items_list.append(SharePrices(**data))
                    
        shares = SharePrices.objects.bulk_create(items_list, ignore_conflicts=True)
        return shares
    
    def handle(self, *args, **options):
        error_text = ('%s\nTry calling generate_seed with --help argument or ' +
                      'use the following arguments:\n %s' % self.args)
        # try:
        fakeEntry = int(options.get('fakeEntry', 0))
        dbName = options.get('dbName', 'default')
        dropDb = options.get('dropDb')
        if not dbName:
            raise CommandError(error_text % 'must pass --dbName')
        elif not self.checkDbConnection(dbName=dbName):
            raise CommandError(f'Error in connecting to the database `{dbName}`')
        try:
            if dropDb:
                self.dbCleaner(dbName)
        except AttributeError:
            raise CommandError("Failed to drop database entry.")
        close_old_connections()
        self.ENTRY = fakeEntry
        self.fakePaymentType(fakeEntry=fakeEntry, dbName=dbName)
        self.fakeSharePrices(fakeEntry=fakeEntry, dbName=dbName)
        self.getStudentUser(fakeEntry=fakeEntry, dbName=dbName)
        self.fakeCourses(fakeEntry=fakeEntry, dbName=dbName)
        self.fakeOrders()
        self.fakeClasses(fakeEntry=fakeEntry, dbName=dbName)
        self.fakeTransactions(fakeEntry=fakeEntry, dbName=dbName)
        self.stdout.write("done\n\n")
        # except Exception as ex:
        # raise CommandError(ex)

    def checkDbConnection(self, dbName):
        db_conn = connections[dbName]
        try:
            db_conn.cursor()
        except OperationalError:
            connected = False
        else:
            connected = True
        return connected

    def dbCleaner(self, dbName):
        confirm = input(
            'You are going to drop the database tables.\nAre you sure? [y|Y] or [n|N]: ')
        if confirm in ['y', 'Y']:
            models = loading.get_models(include_auto_created=False)
            for model in models:
                if model._meta.app_label in ['shares','courses', 'pricing', 'countries', 'users', 'transactions', 'statements', 'coupons']:
                    try:
                        if model == ThkeeUser:
                            model.objects.using(dbName).filter(is_staff=False).delete()
                        else:    
                            model.objects.using(dbName).all().delete()
                    except Exception as ex:
                        print(ex)
        else:
            print('You are safe. :)')

    