from rest_framework import serializers
from apps.courses.models import (
    CourseObjective,
    CourseRequirement,
    CourseLearner,
    )
from django.db import IntegrityError

class CourseIntendedObjectives(serializers.ModelSerializer):
    id = serializers.IntegerField()
    class Meta:
        model = CourseObjective
        fields = ['id', 'content', 'course']
        read_only_fields = ['course']
    
    def update_or_create(self, validated_data, course):
        id_list = []
        objs_to_update = []
        objs_to_create = []

        # Separate objects to update and create based on the presence of id
        for data in validated_data:
            obj_id = data.get('id')
            data['course'] = course
            if obj_id:
                id_list.append(obj_id)
                objs_to_update.append(self.Meta.model(**data))
            else:
                objs_to_create.append(self.Meta.model(**data))

        # Update objects with existing ids
        if objs_to_update:
            self.Meta.model.objects.bulk_update(objs_to_update, fields=['content',])

        # Create objects with no ids
        if objs_to_create:
            try:
                self.Meta.model.objects.bulk_create(objs_to_create)
            except IntegrityError:
                # Handle unique constraint violation error, if any
                pass

        # Return all objects
        queryset = self.Meta.model.objects.filter(course=course)
        return queryset


class CourseIntendedRequirements(serializers.ModelSerializer):
    class Meta:
        model = CourseRequirement
        fields = ['id', 'content', 'course']
        read_only_fields = ['course']
    
    def update_or_create(self, validated_data, course):
        id_list = []
        objs_to_update = []
        objs_to_create = []

        # Separate objects to update and create based on the presence of id
        for data in validated_data:
            obj_id = data.get('id')
            data['course'] = course
            if obj_id:
                id_list.append(obj_id)
                objs_to_update.append(self.Meta.model(**data))
            else:
                objs_to_create.append(self.Meta.model(**data))

        # Update objects with existing ids
        if objs_to_update:
            self.Meta.model.objects.bulk_update(objs_to_update, fields=['content',])

        # Create objects with no ids
        if objs_to_create:
            try:
                self.Meta.model.objects.bulk_create(objs_to_create)
            except IntegrityError:
                # Handle unique constraint violation error, if any
                pass

        # Return all objects
        queryset = self.Meta.model.objects.filter(course=course)
        return queryset

class CourseIntendedLearners(serializers.ModelSerializer):
    class Meta:
        model = CourseLearner
        fields = ['id', 'content', 'course']
        read_only_fields = ['course']
    
    def update_or_create(self, validated_data, course):
        id_list = []
        objs_to_update = []
        objs_to_create = []
        # Separate objects to update and create based on the presence of id
        for data in validated_data:
            obj_id = data.get('id')
            data['course'] = course
            if obj_id:
                id_list.append(obj_id)
                objs_to_update.append(self.Meta.model(**data))
            else:
                objs_to_create.append(self.Meta.model(**data))

        # Update objects with existing ids
        if objs_to_update:
            self.Meta.model.objects.bulk_update(objs_to_update, fields=['content',])

        # Create objects with no ids
        if objs_to_create:
            try:
                self.Meta.model.objects.bulk_create(objs_to_create)
            except IntegrityError:
                print('Handle unique constraint violation error, if any')
                pass

        # Return all objects
        queryset = self.Meta.model.objects.filter(course=course)
        return queryset