from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class CustomLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 10
    max_limit = 15

    def get_paginated_response(self, data):
        context = self.get_html_context()
        
        return Response({
            'total_items': self.count,
            'count_pages': context['page_links'][-1].number,
            'previous': self.get_previous_link(),
            'next': self.get_next_link(),
            'count_items_current_page': len(data),
            'results': data
        })
