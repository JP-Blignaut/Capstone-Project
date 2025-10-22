from django.contrib import admin
from .models import (User, ReaderProfile, JournalistProfile, EditorProfile, 
                     Roles, Publisher, Article, ResetToken)

class PublisherAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_editors_count', 
                    'get_journalists_count']
    search_fields = ['name']
    # This creates a better interface for ManyToMany fields:
    filter_horizontal = ['editors', 'subscribers']  
    
    def get_editors_count(self, obj):
        return obj.editors.count()
    get_editors_count.short_description = 'Editors Count'

    def get_journalists_count(self, obj):
        return obj.journalists.count()
    get_journalists_count.short_description = 'Journalists Count'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Customize the queryset for ManyToMany fields to respect 
        limit_choices_to"""
        if db_field.name == "editors":
            kwargs["queryset"] = User.objects.filter(groups__name='Editors')
        elif db_field.name == "journalists":
            kwargs["queryset"] = User.objects.filter(
                groups__name='Journalists'
                )
        return super().formfield_for_manytomany(db_field, request, **kwargs)








# Register your models here.

admin.site.register(User)
admin.site.register(ReaderProfile)
admin.site.register(JournalistProfile)
admin.site.register(EditorProfile)
admin.site.register(Publisher, PublisherAdmin)  # Use the custom admin class
admin.site.register(Article)
admin.site.register(ResetToken)