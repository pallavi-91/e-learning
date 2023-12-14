import pdb
from intuitlib.client import AuthClient
from quickbooks import QuickBooks
from quickbooks.objects.customer import Customer
from quickbooks.objects.invoice import Invoice
from quickbooks.objects.account import Account
from quickbooks.objects.vendor import Vendor
from quickbooks.objects.taxservice import TaxService, TaxRateDetails
from quickbooks.objects.taxagency import TaxAgency
from quickbooks.objects.detailline import SalesItemLine, SalesItemLineDetail
from quickbooks.exceptions import QuickbooksException
from quickbooks.objects.item import Item
from quickbooks.objects.base import CustomerMemo
from quickbooks.objects.purchaseorder import PurchaseOrder
from django.conf import settings

class QuickbookClient:
    def __init__(self):
        auth_client = AuthClient(
                client_id=settings.QUICKBOOKS_CLIENT_ID,
                client_secret=settings.QUICKBOOKS_CLIENT_SECRET,
                # access_token=settings.QUICKBOOKS_ACCESS_TOKEN,  # If you do not pass this in, the Quickbooks client will call refresh and get a new access token. 
                environment='sandbox',
                redirect_uri='http://localhost:8000/qb/callback',
            )


        self.client = QuickBooks(
                auth_client=auth_client,
                refresh_token=settings.QUICKBOOKS_REFRESH_TOKEN,
                company_id=settings.QUICKBOOKS_COMPANY_ID,
                #minorversion=59 
            )

        self.income_account = Account.where("AccountType = 'Income' and Name='Sales of Product Income'", max_results=1, qb=self.client)[0]
        self.expense_account = Account.where("AccountType = 'Cost of Goods Sold' and Name='Cost of Goods Sold'", max_results=1, qb=self.client)[0]
        self.asset_account = Account.where("AccountType = 'Other Current Asset' and Name='Inventory'", max_results=1, qb=self.client)[0]
        
    def create_account(self, name, account_number, account_type, *args, **kwargs):
        """
            Create a new entry for the account in quickboos
        """
        try:
            account = Account.filter(Name=name, qb=self.client)
            if len(account):
                return account[0]
            # Add customer
            account = Account()
            account.AcctNum = account_number
            account.Name = name
            account.AccountSubType = account_type#"CashOnHand"
            account.save(qb=self.client)
        
            return account
        except QuickbooksException as e:
            print(e.message) # contains the error message returned from QBO
            print(e.error_code) # contains the  
            print(e.detail) #
            
    
    def create_customer(self, first_name, last_name, email, *args, **kwargs):
        """
            Create a new entry for the students as a customer in quickboos
        """
        try:
            full_name = f"{first_name} {last_name}"
            customers = Customer.filter(Active=True, GivenName=email,
                                        FullyQualifiedName=full_name,
                                        FamilyName='Students', 
                                        CompanyName=settings.QUICKBOOKS_COMPANY_ID,
                                        qb=self.client)
            if len(customers):
                return customers[0]
            # Add customer
            customer = Customer()
            customer.GivenName=email
            customer.FullyQualifiedName=full_name
            customer.FamilyName='Students'
            customer.CompanyName=settings.QUICKBOOKS_COMPANY_ID
            customer.save(qb=self.client)
            return customer
        except QuickbooksException as e:
            print(e.message) # contains the error message returned from QBO
            print(e.error_code) # contains the  
            print(e.detail) #

    def create_vendor(self, first_name, last_name, email, *args, **kwargs):
        """
            Create a new entry for the instructor/seller/vendor in quickboos
        """
        try:
            full_name = f"{first_name} {last_name}"
            vendors = Vendor.filter(Active=True, GivenName=email,
                                        DisplayName=full_name,
                                        FamilyName='Instructors',
                                        qb=self.client)
            if len(vendors):
                return vendors[0]
            # Add customer
            vendor = Vendor()
            vendor.GivenName=email
            vendor.DisplayName=full_name
            vendor.FamilyName='Instructors'
            vendor.save(qb=self.client)
            return vendor
        except QuickbooksException as e:
            print(e.message) # contains the error message returned from QBO
            print(e.error_code) # contains the  
            print(e.detail) # contains additional information when available
    
    
    def add_tax_agency(self, country_name):
        taxagency = TaxAgency.filter(DisplayName=country_name)
        if len(taxagency):
            return taxagency[0]
        taxagency = TaxAgency()
        taxagency.DisplayName=country_name
        taxagency.save()
        return taxagency
    
    def create_tax_rate(self, country_name, tax_rate=2, tax_agency_id=1):
        taxservice = TaxService()
        taxservice.TaxCode = country_name # YOUR COUTRY TAX CODE

        tax_rate_detail = TaxRateDetails()
        tax_rate_detail.TaxRateName = country_name # YOUR COUTRY TAX CODE
        tax_rate_detail.RateValue = tax_rate # x% of tax on currency
        tax_rate_detail.TaxAgencyId = tax_agency_id
        tax_rate_detail.TaxApplicableOn = "Sales"   

        taxservice.TaxRateDetails.append(tax_rate_detail)
        created_taxservice = taxservice.save(qb=self.client)
        return created_taxservice
    
    def create_invoice(self, payload, *args, **kwargs):
        """
         For the transaction of order type we need to add a new invoice for the student.
         payload = {
             "title": "Testing course purchase",
             "gross_amount": 100,
             "transaction_id": "TRAN432432432",
             "course": [{
                 "title": "Testing course purchase",
                 "date_created": datetime.datetime(2023,1,2,12,22,0),
                 "id": 23,
                 "price": 100
             }]
         }
        """
        invoice = Invoice()
        line = SalesItemLine()
        line.LineNum = 1
        line.Description = payload.get('title')
        line.Amount = payload.get('gross_amount')
        line.SalesItemLineDetail = SalesItemLineDetail()
        
        item = self.add_or_get_product(payload.get('course'))
        
        line.SalesItemLineDetail.ItemRef = item.to_ref()
        invoice.Line.append(line)
        
        customer = None # Get customer/student account
        invoice.CustomerRef = customer.to_ref()
        invoice.CustomerMemo = CustomerMemo()
        invoice.CustomerMemo.value = "Customer Memo"
        invoice.save(qb=self.client, request_id=payload.get('transaction_id'))
    
    def add_or_get_product(self, course, *args, **kwargs):
        """
        An item is a thing that your company buys, sells, or re-sells, such as products and services.
        course = {
                 "title": "Testing course purchase",
                 "date_created": datetime.datetime(2023,1,2,12,22,0),
                 "id": 23,
                 "price": 100
             } 
        """
        
        
        items = Item.filter(Type='Service', Sku = str(course.get('id')), max_results=1, qb=self.client)
        if len(items):
            return items[0]
        
        item = Item()
        item.Name = course.get('title')
        item.Description = course.get('description')
        item.Type = "Service"
        item.UnitPrice = course.get('price')
        # item.TrackQtyOnHand = True
        # item.QtyOnHand = 10000
        item.Sku = str(course.get('id'))
        item.InvStartDate = course.get('date_updated').strftime('%Y-%m-%d')#"2015-01-01"

        item.IncomeAccountRef = self.income_account.to_ref()
        item.ExpenseAccountRef = self.expense_account.to_ref()
        item.AssetAccountRef = self.asset_account.to_ref()
        item.save(qb=self.client)
        
        query_item = Item.get(item.Id, qb=self.client)
        return query_item