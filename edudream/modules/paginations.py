from rest_framework import pagination


class CustomPagination(pagination.PageNumberPagination):
    page_size = 30
    max_page_size = 100


class AdminPagination(pagination.PageNumberPagination):
    page_size = 10
    max_page_size = 15

