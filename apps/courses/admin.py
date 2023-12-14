from django.contrib import admin
from .models import (Scope, 
                Section, 
                SubSection, 
                Course, 
                Lecture, 
                SubCategory, 
                Category, 
                SubsectionProgress,
                Quiz,
                QuizQuestion,
                QuizAnswer,
                Assignment,
                AssignmentQuestion,
)

from nested_inline.admin import NestedStackedInline, NestedModelAdmin

# ================  Model Registrations ================

class QuizAnswerInline(NestedStackedInline):
    """ Quiz answers"""
    model = QuizAnswer
    extra = 0

class QuizQuestionInline(NestedStackedInline):
    """ Quiz answers"""
    model = QuizQuestion
    extra = 0
    inlines = [QuizAnswerInline]

@admin.register(Quiz)
class QuizAdmin(NestedModelAdmin):
    list_display = ('id', 'title', 'date_updated',)
    inlines = [QuizQuestionInline]


class ScopeInline(admin.StackedInline):
    """ course scope admin
    """
    model = Scope
    extra = 0

class SectionInline(admin.StackedInline):
    """ section admin
    """
    model = Section
    extra = 0
    show_change_link = True
    
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """ course admin config
    """
    list_display = ('title', 'code', 'user','category', 'status', 'date_updated',)
    search_fields = ('title', 'code', 'category__name')
    inlines = (ScopeInline, SectionInline)
    list_filter = ['status']

@admin.register(SubSection)
class SubSectionAdmin(admin.ModelAdmin):
    list_display = ('type', 'section', 'position', 'quiz', 'lecture', 'assignment', 'date_created', 'date_updated')

class LectureInline(admin.StackedInline):
    model = Lecture
    extra = 0

class SubSectionInline(admin.StackedInline):
    model = SubSection
    extra = 0

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'position', 'date_created', 'date_updated')
    search_fields = ('title', 'course__title', 'course__id')
    inlines = [LectureInline, SubSectionInline]
    

@admin.register(SubsectionProgress)
class SubsectionProgressAdmin(admin.ModelAdmin):
    list_display = ['__str__','date_created']


class SubCategoryInline(admin.StackedInline):
    model = SubCategory
    readonly_fields=('slug', )
    extra = 0

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """ course category admin config
    """
    list_display = ('name', 'get_subcategories', 'slug',)
    search_fields = ('name',)
    readonly_fields=('slug', )
    inlines = (SubCategoryInline,)

    def get_subcategories(self, instance):
        """ list sub categories
        """
        return ", ".join(
            instance.subcategories.values_list('name', flat=True))

    get_subcategories.short_description = "Sub categories"
