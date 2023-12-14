from django.db.models.functions import Lower
from django.db.models import F
from rest_framework.filters import OrderingFilter


class IOrderingFilter(OrderingFilter):
    """Case insensitive filter"""
    def remove_invalid_fields(self, queryset, fields, view, request):
        valid_fields = [item[0] for item in self.get_valid_fields(queryset, view, {'request': request})]

        def term_valid(term):
            if term.startswith("-"):
                term = term[1:]

            if term.endswith("-i"):
                term = term[0:-2]

            return term in valid_fields

        return [term for term in fields if term_valid(term)]


    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            new_ordering = []
          
            for field in ordering:
                # Case insensitive order
                if not field.endswith('-i'): 
                    if field[0] == '-':
                        new_ordering.append(F(field[1:]).desc(nulls_last=True))
                    else:
                        new_ordering.append(F(field).asc(nulls_last=True))
                else:
                    field = field[0:-2]
                    if field.startswith('-'):
                        new_ordering.append(Lower(field[1:]).desc())
                    else:
                        new_ordering.append(Lower(field).asc())
            return queryset.order_by(*new_ordering)

        return queryset