from rest_framework.pagination import CursorPagination, PageNumberPagination

class CoursePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'


class ClassPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

class SubsectionPagination(CursorPagination):
    page_size = 20
    cursor_query_param = 'page'
    ordering = "position"
    
class SectionPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    page_size = 20    

class QuizPagination(SubsectionPagination):
    pass


class AssignmentPagination(CoursePagination):
    pass


class ShortLecturePagination(SubsectionPagination):
    pass

class CourseReviewPagination(ClassPagination):
    pass


class CourseSubmissionPagination(ClassPagination):
    pass

class StudentAssignmentPagination(ClassPagination):
    pass


class CourseAnnouncementPagination(ClassPagination):
    pass


class CourseRejectPagination(ClassPagination):
    pass


class CoursePricePagination(ClassPagination):
    pass

class NotePagination(ClassPagination):
    page_size = 10


class SubsectionProgressPagination(ClassPagination):
    page_size = 10


class TopicPagination(ClassPagination):
    page_size = 15