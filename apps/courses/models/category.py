from django.db import models
from django.utils.translation import gettext as _
from apps.courses.models.sections import SubSection
from apps.status import CourseLectureType
from apps.status.mixins import AutoCreatedUpdatedMixin
from apps.utils.slugify import unique_slugify

class Category(AutoCreatedUpdatedMixin):
    """ category
    """
    class Meta:
        db_table = 'course_category'
        verbose_name_plural = "Categories"
        
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=500,null=True,blank=True)
    icon = models.CharField(max_length=10, blank=True)
    
    def __str__(self):
        return f"{self.name}"

    def save(self, **kwargs):
        unique_slugify(self, self.name) 
        return super(Category, self).save(**kwargs)


class SubCategory(AutoCreatedUpdatedMixin):
    """ subcategory
    """
    class Meta:
        db_table = 'course_subcategory'
        verbose_name_plural = "Sub Categories"
        
    category = models.ForeignKey(Category, related_name="subcategories", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=500,null=True,blank=True)

    def __str__(self):
        return f"{self.name}"

    @property
    def duration(self):
        subsections = self.subsections.filter(type=SubSection.LECTURE)
        total = 0
        for sub in subsections:
            if sub.lecture.type == CourseLectureType.VIDEO:
                total += self.lecture.video_info['duration']
            else:
                total += self.lecture.article_info['duration']

        return 0

    def save(self, **kwargs):
        unique_slugify(self, self.name) 
        return super(SubCategory, self).save(**kwargs)