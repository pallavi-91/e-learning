from django.db.utils import OperationalError
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from django.db.utils import IntegrityError
from apps.shares.models import SharePrices, InstructorGroups, ShareTypes



class Command(BaseCommand):
    args = '<[--dropDb | -d]>'
    help = """
           Generate fixtures
           for a given object, generate json fixtures to rediret
           to a file in order to have full hierarchy of models
           from this parent object.
           syntax example:
               python manage.py generate_seed --dropDb
           """

    def add_arguments(self, parser):
        """Add command line arguments to parser"""
        super().add_arguments(parser)
        # Required Args

        parser.add_argument('--dropDb', '-d',
                            action='store_const',
                            dest='dropDb',
                            const=True,
                            help='Drop all the existing entry')

    def sharesEntry(self):
        self.stdout.write('Generating seed data for share pricing')
        shares = []
        for share_type, _ in ShareTypes.choices:
            if share_type in [ShareTypes.ORGANICS, ShareTypes.ADS, ShareTypes.INSTRUCTOR_REFERRAL]:
                for group_name, _ in InstructorGroups.choices:
                    obj = SharePrices(share_types=share_type,
                                      instructor_share=40,
                                      platform_share=60,
                                      group_name=group_name)
                    shares.append(obj)
            elif share_type == ShareTypes.AFFILIATE:
                obj = SharePrices(share_types=share_type,
                                    instructor_share=40,
                                    platform_share=55,
                                    affiliate_share=5)
                shares.append(obj)
            elif share_type == ShareTypes.STUDENT_REFERRAL:
                obj = SharePrices(share_types=share_type,
                                    instructor_share=40,
                                    platform_share=55,
                                    thkee_credit=5)
                shares.append(obj)
        
        if shares:
            SharePrices.objects.bulk_create(shares)

    def handle(self, *args, **options):
        try:
            dropDb = options.get('dropDb')
            if dropDb:
                self.sharesCleaner()
            else:
                raise Exception("Please drop previous entry, pass argument -d.")
            self.sharesEntry()
            self.stdout.write("done\n\n")
        except Exception as ex:
            raise CommandError(ex)

    def sharesCleaner(self):
        confirm = input(
            'You are going to drop the database tables.\nAre you sure? [y|Y] or [n|N]: ')
        if confirm in ['y', 'Y']:
            try:
                SharePrices.objects.all().delete()
            except Exception as ex:
                print(ex)
        else:
            print('You are safe. :)')
