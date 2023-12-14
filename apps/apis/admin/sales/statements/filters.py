from rest_framework.filters import SearchFilter

class StatementSearchFilter(SearchFilter):
    search_param = 'search'