from rest_framework.filters import OrderingFilter


class ProductOrderingFilter(OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        ordering_params = request.query_params.get(self.ordering_param)
        valid_fields = [field[0] for field in self.get_valid_fields(queryset, view, request)]
        
        if ordering_params:
            fields = [param.strip() for param in ordering_params.split(',')]
            ordering = []
            
            for field in fields:
                field_name, direction = self.get_field_ordering_and_direction(field)
                if field_name in valid_fields:
                    ordering.append(f'{direction}{field_name}')
            
            if ordering:
                return queryset.order_by(*ordering)

        return super().filter_queryset(request, queryset, view)
    
    def get_field_ordering_and_direction(self, ordering_param):
        ordering_parts = ordering_param.split('-')
        
        if len(ordering_parts) == 2 and ordering_parts[1] in ('asc', 'desc'):
            return ordering_parts[0], '-' if ordering_parts[1] == 'desc' else ''
        return ordering_param, ''