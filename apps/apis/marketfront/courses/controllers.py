import requests
from django.conf import settings
from django.shortcuts import get_object_or_404

from django.utils.translation import gettext as _
from django.db import transaction
from django.db.models import Count 

from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework.filters import OrderingFilter,SearchFilter
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.exceptions import ValidationError
from apps.status import CourseStatus
from apps.users.tasks import class_generate_certificate
from .filters import CategoryFilter, CourseFilter, NotesFilter, QnAFilter, QnaOrderingFilter
from apps.courses.paginations import CourseAnnouncementPagination, CoursePagination, ClassPagination, CoursePricePagination, CourseRejectPagination, CourseReviewPagination, CourseSubmissionPagination, NotePagination, TopicPagination
from apps.users.models import  UserClass
from apps.courses.models import Course, QnA, QnAReplys, CourseView, Topic,SubCategory
from rest_framework import status
from django_filters import rest_framework as filters
from apps.utils.cloudflare import CloudflareStream
from apps.utils.filters import IOrderingFilter
from apps.apis.marketfront.users.serializers import InstructorUserSerializer
from apps.utils.query import SerializerProperty, get_object_or_none
from apps.utils.paginations import ViewSetPagination
from django.db.models import Avg, Case, Count, F, Sum, When, FloatField, Value, Q, Max
from django.db.models.functions import Coalesce, Round
from rest_framework import viewsets
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .serializers import (
    AdminCourseSerializer,
    CourseActionSerializer,
    CourseAnnouncementSerializer,
    CourseDetailSerializer,
    CoursePriceSerializer,
    CourseRejectSerializer,
    CourseReviewSerializer,
    CourseSerializer,
    CategorySerializer,
    CourseSubmissionSerializer,
    CourseViewSerializer,
    MarketplaceCountSerializer,
    MarketplaceSlugSerializer,
    MyCourseReviewSerializer,
    NoteSerializer,
    ReportedCourseReviewSerializer,
    ReportedQnaReplySerializer,
    ReviewSubmissionSerializer,
    LectureSerializer,
    SubCategorySerializer,
    SubSectionSerializer,
    TopicSerializer,
    CourseQnASerializer,
    CourseQnAReplySerializer
)


class CoursesView(SerializerProperty, ViewSetPagination, GenericViewSet):
    """ courses
    """
    serializer_class = CourseSerializer
    pagination_class = CoursePagination 
    filter_backends = [IOrderingFilter,SearchFilter,filters.DjangoFilterBackend]
    filterset_class  = CourseFilter
    search_fields = ['title','subtitle','desc']
    ordering_fields = ['title','date_published','pricing__tier_level','pricing__price']

    public_actions = [
            'list',
            'courses_sub_slug',
            'courses_cat_slug',
            'courses_topic_slug',
            'get','instructor_courses',
            'filters_count']


    def filters_count(self,request):
        serializer = MarketplaceCountSerializer(context=self.get_serializer_context())
        
        return Response(serializer.counts())

    def get_queryset(self):
        qs = self._model.objects.filter(is_deleted=False, status=CourseStatus.STATUS_PUBLISHED)
        return qs 

    
    def instructor(self,request,*args, **kwargs):
        # Get Instructor of course
        instance = get_object_or_404(self._model, **kwargs)
        serializer = InstructorUserSerializer(instance.user)
        return Response(serializer.data)
    
    # @method_decorator(cache_page(60*2, key_prefix='courses-list'))
    def list(self, request):
        """All published courses"""        
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def my_courses(self, request):
        """ instructor courses
        """
        queryset = self.filter_queryset(
            self.get_queryset().filter(
                user=request.user
            )
        )
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def delete(self,request,**kwargs):
        instance=get_object_or_404(self._model,
            user=request.user, **kwargs,is_deleted=False)

        if instance.date_published:
            raise exceptions.PermissionDenied()

        instance.is_deleted = True
        instance.save()
        return Response()

    def create(self, request):
        serializer = self.get_serializer(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        return Response(serializer.data, status=201)

    def edit(self, request, **kwargs):
        course = get_object_or_404(self._model,user=request.user, **kwargs)
        if not course.is_editable:
            raise exceptions.PermissionDenied()

        serializer = self.get_serializer(
            data=request.data,
            partial=True,
            instance=course
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=204)

    @transaction.atomic
    def get(self, request, **kwargs):
        """Get course and count the number of views"""
        qs = self.get_queryset()
        view_serializer = CourseViewSerializer(context=self.get_serializer_context())
        course = get_object_or_404(qs,**kwargs)

        serializer = CourseDetailSerializer(instance = course, context=self.get_serializer_context())
        view_serializer.get_or_create(course)

        return Response(serializer.data, status=200)

    def request_edit(self,request,**kwargs):
        course = get_object_or_404(self._model,user=request.user, **kwargs)
        if course.status != CourseStatus.STATUS_INREVIEW:
            raise exceptions.PermissionDenied()
        course.status = course.STATUS_DRAFT
        course.save()
        return Response()

    def courses_sub_slug(self,request,**kwargs):
        """ get courses by subcategory slug and related topics """
        sub = get_object_or_404(SubCategorySerializer.Meta.model,**kwargs)
        data = MarketplaceSlugSerializer(context=self.get_serializer_context())\
                .slug_data(title=sub.name,slug=sub.slug)

        return Response(data)

    def courses_topic_slug(self,request,**kwargs):
        """ get courses by topic slug and related topics """
        topic = get_object_or_404(TopicSerializer.Meta.model,**kwargs)
        data = MarketplaceSlugSerializer(context=self.get_serializer_context())\
                .slug_data(title=topic.name,slug=topic.slug)

        return Response(data)

    def courses_cat_slug(self,request,**kwargs):
        """ get courses by category slug and related topics """
        cat = get_object_or_404(CategorySerializer.Meta.model,**kwargs)
        data = MarketplaceSlugSerializer(context=self.get_serializer_context())\
            .slug_data(title=cat.name,slug=cat.slug)

        return Response(data)

    @transaction.atomic
    def toggle_favorite(self,request,**kwargs):
        """Free course cannot be in the wishlist or favorites"""
        qs = self.get_queryset()
        course = get_object_or_404(qs,**kwargs)
        
        if request.user.favorites.filter(id=course.id).count():
            request.user.favorites.remove(course)
        else:
            request.user.favorites.add(course)
            
        serializer = self.serializer_class(course, context=self.get_serializer_context())
        return Response(data=serializer.data, status=201)

    def my_favorites(self,request,**kwargs):
        """ get wishlist or favorites 
        """
        page = self.paginate_queryset(self.filter_queryset(request.user.favorites.all()))
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    

class CategoriesView(SerializerProperty, ViewSetPagination, GenericViewSet):
    """ course categories
    """
    public_actions = ['list', 'top_category']
    serializer_class = CategorySerializer
    pagination_class = ClassPagination
    filter_backends = (filters.DjangoFilterBackend,SearchFilter)
    search_fields = ['name'] 
    filterset_class = CategoryFilter

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self._model.objects.prefetch_related('subcategories', 'courses').filter(**kwargs))
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page,many=True)
        return Response(serializer.data, status=200)
    
    def used_category(self,request):
        """get all the used categories and subcategories for filtering """
        categories = self._model.objects.prefetch_related('subcategories','courses').filter(courses__user=request.user).distinct('id')
        subcategories = SubCategorySerializer.Meta.model.objects.select_related('category').filter(courses__user=request.user).distinct('id')
        fields = ['id','name']
        return Response({
            'categories': self.get_serializer(categories,fields=fields,many=True).data,
            'subcategories': SubCategorySerializer(subcategories,fields=fields,many=True).data,
        })
    
    def top_category(self, request, *args, **kwargs):
        top_categories_list = UserClass.objects.values('course').annotate(courses = Count('course')).order_by('-courses').values('course__category')
        if not top_categories_list:
            queryset = self._model.objects.prefetch_related('subcategories','courses').annotate(count_courses=Count('courses')).order_by('-count_courses')
        else:
            queryset = self._model.objects.prefetch_related('subcategories','courses').filter(id__in=top_categories_list)
        
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page,many=True)
        return Response(serializer.data, status=200)

class SubcategoriesView(ModelViewSet):
    serializer_class = SubCategorySerializer
    queryset = SubCategory.objects.all()
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset().filter(category=kwargs.get('category')))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    

class CourseReviewView(SerializerProperty, ViewSetPagination, GenericViewSet):

    serializer_class = CourseReviewSerializer
    pagination_class = CourseReviewPagination
    filter_backends = [OrderingFilter,SearchFilter]
    ordering_fields = ['date_created','rate']
    search_fields = ['content','course__title','user__first_name']
    public_actions = ['list', 'student_feedbacks']

    def get_queryset(self):
        return self.filter_queryset(self._model.objects.select_related('course').prefetch_related('likes','reports').filter(course__code=self.kwargs.get('code')))
        
    def create(self,request, **kwargs):
        course = get_object_or_404(CourseSerializer.Meta.model, **kwargs, is_deleted=False)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course, user=request.user)
        return Response(serializer.data)

    def list(self,request,**kwargs):
        """ get the course reviews by course id on view course """
        qs = self.filter_queryset(self.get_queryset()) 
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    def get_my_ratings(self,request,**kwargs):
        reviews = self.get_queryset().filter(course__user=request.user, course__is_deleted=False)
        qs = self.filter_queryset(reviews) 
        page = self.paginate_queryset(qs)
        serializer = MyCourseReviewSerializer(page, many=True, context=self.get_serializer_context())
        return self.get_paginated_response(serializer.data)
    
    def student_feedbacks(self,request,**kwargs):
        course = get_object_or_404(CourseSerializer.Meta.model, **kwargs, is_deleted=False)
        reviews = self._model.objects.filter(course=course).aggregate(
                                            avg_rating = Avg('rate'),
                                            total_reviews=Count('id'),
                                            five_star_ratings = Count(Case(When(rate=5, then='id'))),
                                            four_star_ratings = Count(Case(When(rate=4, then='id'))),
                                            three_star_ratings = Count(Case(When(rate=3, then='id'))),
                                            two_star_ratings = Count(Case(When(rate=2, then='id'))),
                                            one_star_ratings = Count(Case(When(rate=1, then='id'))),
                                        )
        
        return Response(reviews)

    def like_review(self,request,**kwargs):
        review = get_object_or_404(self._model, **kwargs)
        serializer = CourseActionSerializer(instance=review)
        return Response({ 'like': serializer.like(request.user) })

    def dislike_review(self,request,**kwargs):
        review = get_object_or_404(CourseActionSerializer.Meta.model, **kwargs)
        serializer = CourseActionSerializer(instance=review)
        return Response({ 'dislike': serializer.dislike(request.user) })

    def report_review(self,request,**kwargs):
        review = get_object_or_404(CourseActionSerializer.Meta.model, **kwargs)
        if review.reports.filter(user=request.user).count():
            raise ValidationError(_('You already report this review'))
        
        serializer = ReportedCourseReviewSerializer(data = request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save(review=review, user=request.user)
        return Response(serializer.data)
    
    def review_reportes(self,request,**kwargs):
        review = get_object_or_404(CourseActionSerializer.Meta.model, **kwargs)
        qs = review.reports.all()
        page = self.paginate_queryset(qs)
        serializer = ReportedCourseReviewSerializer(page, many=True, context=self.get_serializer_context())
        return self.get_paginated_response(serializer.data)


class CourseSubmissionView(SerializerProperty, ViewSetPagination, GenericViewSet):

    serializer_class = CourseSubmissionSerializer
    pagination_class = CourseSubmissionPagination
    filter_backends = [OrderingFilter,SearchFilter]
    ordering_fields = ['date_created','rate']
    search_fields = ['title']

    def list(self,request,**kwargs):
        qs = self.filter_queryset(
                request.user.courses.filter(
                    is_deleted=False,
                    status=CourseStatus.STATUS_PUBLISHED)
                    .order_by('-date_updated')
        ) 
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page,many=True)
        return self.get_paginated_response(serializer.data)

    def review_questions(self,request):
        serializer = ReviewSubmissionSerializer(data=request.data,context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.feedback()
        return Response(status=status.HTTP_200_OK)



class ForReviewCourseView(SerializerProperty, ViewSetPagination, GenericViewSet):
    permission_classes = [IsAdminUser]

    serializer_class = AdminCourseSerializer

    public_actions = ['get_course']

    def get_course(self, request, **kwargs):

        if request.user.is_staff:
            course = get_object_or_404(self.serializer_class.Meta.model,**kwargs)
        elif request.user.is_authenticated:
            course = get_object_or_404(request.user.courses.all(),**kwargs)
        else:
            return Response(status=404)

        return Response(self.get_serializer(course).data) 

    def approve(self,request,**kwargs):
        course = get_object_or_404(CourseSerializer.Meta.model,**kwargs)
        self._raise_if_draft(course)
        course.approve()
        return Response(status=200) 

    def _raise_if_draft(self,course):
          if course.status in [course.STATUS_DRAFT]:
            raise exceptions.PermissionDenied(_('This course is currently in draft'))

    @transaction.atomic
    def reject(self,request,**kwargs):
        course = get_object_or_404(CourseSerializer.Meta.model,**kwargs)
        
        self._raise_if_draft(course)

        serializer = CourseRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course,user=request.user)
        course.status = course.STATUS_REJECTED
        course.save()
        return Response(status=200) 
        

class CourseAnnouncementView(SerializerProperty, ViewSetPagination, ModelViewSet):

    serializer_class = CourseAnnouncementSerializer
    pagination_class = CourseAnnouncementPagination
    filter_backends = (SearchFilter, OrderingFilter,)
    ordering_fields = ['date_created','date_updated']

    def get_queryset(self):
        return self.request.user.course_announcements.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user,**self.kwargs)

    def course_announcements(self,request, **kwargs):
        page = self.paginate_queryset(
            self.filter_queryset(self._model.objects.filter(**kwargs))
        )
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()       
        serializer = CourseAnnouncementSerializer (instance = instance)
        return Response(serializer.data)

    
class CourseRejectView(SerializerProperty, ViewSetPagination, ModelViewSet):

    serializer_class = CourseRejectSerializer
    pagination_class = CourseRejectPagination
    filter_backends = (SearchFilter, OrderingFilter,)
    ordering_fields = ['date_created','date_updated']

    permission_classes = [IsAdminUser]
    permission_classes_by_action = {
        'course_rejects': [IsAuthenticated]
    }

    def get_queryset(self):
        return self._model.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user,**self.kwargs)

    def course_rejects(self,request, **kwargs):
        page = self.paginate_queryset(
            self.filter_queryset(self._model.objects.filter(**kwargs))
        )
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    
class CoursePriceView(SerializerProperty, ViewSetPagination, ModelViewSet):

    serializer_class = CoursePriceSerializer
    pagination_class = CoursePricePagination
    filter_backends = (SearchFilter, OrderingFilter,)
    ordering_fields = ['date_created','date_updated']

    def get_queryset(self):
        return self._model.objects.order_by('tier_level')



class NoteView(SerializerProperty, ViewSetPagination, ModelViewSet):
    """Current User's purchased class notes"""
    serializer_class = NoteSerializer
    pagination_class = NotePagination
    filter_backends = (SearchFilter, OrderingFilter, filters.DjangoFilterBackend)
    filterset_class = NotesFilter
    ordering_fields = ['date_updated']

    def get_queryset(self):
        qs = self.request.user.notes.prefetch_related('subsection','subsection__section').filter(user_class_id=self.kwargs.get('user_class_id'))
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user,**self.kwargs)

    def list(self,request,**kwargs):
        notes = self.get_queryset()
    
        queryset = self.filter_queryset(notes)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)



class UploadVideo(SerializerProperty, ViewSetPagination, GenericViewSet):
    public_actions = ['upload']
    serializer_class = LectureSerializer
    
    def upload(self,request):
        url = f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/stream?direct_user=true"
        cors_headers = {
            'Access-Control-Expose-Headers': 'Location',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
        }   

        response = requests.post(url,headers={
            **cors_headers,
            'Authorization': f'Bearer {settings.CLOUDFLARE_API_TOKEN}',
            'Tus-Resumable': '1.0.0',
            'Upload-Length': request.headers.get('Upload-Length'),
            'Upload-Metadata': request.headers.get('Upload-Metadata'),
        })

        response.raise_for_status()
        response.headers.pop('Connection')
        return Response(None,headers=response.headers)

    def update_video_info(self,request,**kwargs):
        _sub_model = SubSectionSerializer.Meta.model
        subsections = _sub_model.objects.filter(section__course__user=request.user)
        subsection = get_object_or_404(subsections,**kwargs)

        if subsection.type != _sub_model.LECTURE  or subsection.lecture.video_id == None:
            raise exceptions.ValidationError(_('Invalid lecture'))

        lecture = subsection.lecture
        # lecture.video_info = CloudflareStream().get_read_info(lecture.video_id) 
        lecture.save()
        return Response(LectureSerializer(lecture,context=self.get_serializer_context()).data)


class TopicView(SerializerProperty,ViewSetPagination,ModelViewSet):
    serializer_class = TopicSerializer
    pagination_class = TopicPagination
    filter_backends = [SearchFilter,OrderingFilter]
    ordering_fields = ('name','courses_count')
    public_actions = ['list']
    search_fields = ['name']

    def get_queryset(self):
        return self._model.objects.annotate(courses_count=Count('courses')).order_by('-courses_count')
    
    def most_searched_topics(self,request):
        views = CourseView.objects.select_related('course').prefetch_related('course__topics').values_list('course__topics__id').distinct()
        topics = Topic.objects.filter(id__in = views)
        serializer = TopicSerializer(topics, many= True)
        return Response(serializer.data)
        
    
class CourseQnAView(SerializerProperty, ViewSetPagination, viewsets.ModelViewSet):
    serializer_class = CourseQnASerializer
    pagination_class = TopicPagination
    filter_backends = [SearchFilter, QnaOrderingFilter, filters.DjangoFilterBackend]
    filterset_class = QnAFilter
    ordering_fields = ['date_updated', 'upvoted']
    search_fields = ['title', 'qnas__comment']
    queryset = QnA.objects.all()


    def get_queryset(self):
        return super().get_queryset().filter(**self.kwargs)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user,**self.kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def toggle_upvoting(self,request,**kwargs):
        """QnA of course upvoted_qna"""
        qs = self.get_queryset()
        instance = get_object_or_404(qs,**kwargs)
        
        if request.user.upvoted_qna.filter(id=instance.id).count():
            request.user.upvoted_qna.remove(instance)
        else:
            request.user.upvoted_qna.add(instance)
            
        serializer = self.get_serializer(instance)
        return Response(data=serializer.data, status=201)
    
class CourseQnAReplyView(SerializerProperty, ViewSetPagination, viewsets.ModelViewSet):
    serializer_class = CourseQnAReplySerializer
    pagination_class = TopicPagination
    queryset = QnAReplys.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user,**self.kwargs)
        
    def get_queryset(self):
        return super().get_queryset().filter(**self.kwargs)


    def toggle_upvoting(self,request,**kwargs):
        """QnA of course upvoted_qna_reply"""
        qs = self.get_queryset()
        instance = get_object_or_404(qs,**kwargs)
        
        if request.user.upvoted_qna_reply.filter(id=instance.id).count():
            request.user.upvoted_qna_reply.remove(instance)
        else:
            request.user.upvoted_qna_reply.add(instance)
            
        serializer = self.get_serializer(instance)
        return Response(data=serializer.data, status=201)
    
    def report_reply(self, request, **kwargs):
        qs = self.get_queryset()
        instance = get_object_or_404(qs,**kwargs)
        serializer = ReportedQnaReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(reply=instance,user=request.user)
        return Response(data=serializer.data, status=201)