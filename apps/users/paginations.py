
from rest_framework.pagination import CursorPagination, PageNumberPagination


class PurchaseHistoryPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'


class ReportPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'


class TransactionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'


class ImageUploadPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'


class RefundRequestPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

