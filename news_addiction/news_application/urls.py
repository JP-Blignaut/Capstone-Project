from django.urls import path
from . import views
urlpatterns = [
    
    # Login and password management:
    path('', views.login_view, name='home_page'),
    path('login/', views.login_view, name='login_page'),
    path('logout/', views.logout_view, name='logout_page'),
    path('register/', views.register_new_user_view,
         name='register_new_user_page'
         ),
    path('request_reset_password/', views.request_reset_password_view,
         name='request_reset_password_page'
         ),
    path('reset_password/<str:token>/', views.reset_user_password_view,
         name='password_reset'
         ),

     # Reader URLs:
    path('reader_start/', views.reader_start_view, name='reader_start_page'),
    path('reader_view_article/<int:article_id>/',
         views.reader_view_article,
         name='reader_view_article_page'
         ),
     path('reader_view_journalist_details/<int:journalist_id>/'
               '<int:article_id>/',
               views.reader_view_journalist_details,
               name='reader_view_journalist_details_page'
         ),
     path('reader_view_journalist_details_subscribe/<int:journalist_id>/'
           '<int:article_id>/',
         views.reader_journalist_subscribe_unsubscribe,
         name='reader_journalist_subscribe_unsubscribe_page'
         ),
     path('reader_view_publisher_details/<int:article_id>/',
         views.reader_view_publisher_details,
         name='reader_view_publisher_details_page'
         ),
     path('reader_view_publisher_details_subscribe/<int:publisher_id>/'
          '<int:article_id>/',
         views.reader_publisher_subscribe_unsubscribe,
         name='reader_publisher_subscribe_unsubscribe_page'
         ),

     # Journalist URLs:
    path('journalist_start/', views.journalist_start_view, 
         name='journalist_start_page'
         ),
     path('journalist_article_management/',
          views.journalist_article_management_view,
          name='journalist_article_management_page'
          ),
     path('journalist_article_detail/<int:pk>/',
          views.journalist_article_detail_view,
          name='journalist_article_detail_page'
          ),
     path('journalist_article_form/new', views.journalist_article_add_view, 
         name='journalist_article_add_page'
         ),
     path('journalist_article_form/<int:pk>/edit',
          views.journalist_article_edit_view,
         name='journalist_article_edit_page'
         ),
     path('journalist_article_delete/<int:pk>',
          views.journalist_article_delete_view,
         name='journalist_article_delete_page'
         ),

     path('journalist_article_form/<int:pk>/publish',
          views.journalist_article_publish_view,
          name='journalist_article_publish_page'
          ),

     # Editor URLs:
     path('editor_start/', views.editor_start_view, 
         name='editor_start_page'),

     path('editor_publisher_dashboard/<int:pk>/', 
          views.editor_publisher_dashboard_view, 
          name='editor_publisher_dashboard_page'
          ),

     path('editor_journalist_management/<int:pk>/', 
          views.editor_journalist_management_view, 
          name='editor_journalist_management_page'
          ),

     path('editor_assign_journalist_form/<int:pk>/', 
          views.editor_assign_journalist_view, 
          name='editor_journalist_assign_page'
          ),   

     path('editor_journalist_remove_assignment_confirm/<int:publisher_pk>/'
          '<int:journalist_pk>/', 
          views.editor_journalist_remove_assignment_view, 
          name='editor_journalist_remove_assignment_page'
          ),

     path('editor_article_management/<int:pk>/', 
          views.editor_article_management_view, 
          name='editor_article_management_page'
          ),
     
     path('editor_article_detail/<int:pk>/',
          views.editor_article_detail_view,
          name='editor_article_detail_page'
          ),

     path('editor_article_form/<int:pk>/edit',
          views.editor_article_edit_view,
         name='editor_article_edit_page'
         ),

     path('editor_article_delete/<int:pk>',
          views.editor_article_delete_view,
         name='editor_article_delete_page'
         ),

       path('editor_article_reject_for_publication/<int:pk>/',
            views.editor_reject_for_publication_view,
            name='editor_article_reject_for_publication_page'
         ),
     
      path('editor_article_accept_for_publication/<int:pk>/',
            views.editor_accept_for_publication_view,
            name='editor_article_accept_for_publication_page'
         ),

     # API Endpoints:
     path('get/articles/', views.API_get_articles, 
          name='API_get_articles_page'),
]
