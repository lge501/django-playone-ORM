from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
]

urlpatterns += [
    path('courts/', views.CourtListView.as_view(), name='court-list'),
    path('court/create/', views.CourtCreateView.as_view(), name='court-create'),
    path('court/<int:pk>', views.CourtDetailView.as_view(), name='court-detail'),
]

urlpatterns += [
    path('groups/', views.GroupListView.as_view(), name='group-list'),
    path('group/create/', views.GroupCreateView.as_view(), name='group-create'),
    path('group/<int:pk>', views.GroupDetailView.as_view(), name='group-detail'),
    path('group/<int:pk>/update', views.GroupUpdateView.as_view(), name='group-update'),
    path('group/<int:pk>/delete', views.GroupDeleteView.as_view(), name='group-delete'),
    path('group/<int:pk>/join', views.group_join, name='group-join'),
    path('group/<int:pk>/quit', views.group_quit, name='group-quit'),
    path('group/<int:pk>/event/create', views.GroupEventCreateView.as_view(), name='group-event-create'),
    path('membership/<int:pk>/delete', views.membership_delete, name='membership-delete'),
    path('membership/<int:pk>/member', views.membership_to_member, name='membership-member'),
    path('membership/<int:pk>/admin', views.membership_to_admin, name='membership-admin'),
]

urlpatterns += [
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('event/create/', views.EventCreateView.as_view(), name='event-create'),
    path('event/<int:pk>', views.EventDetailView.as_view(), name='event-detail'),
    path('event/<int:pk>/update', views.EventUpdateView.as_view(), name='event-update'),
    path('event/<int:pk>/delete', views.EventDeleteView.as_view(), name='event-delete'),
    path('event/<int:pk>/signup', views.event_signup, name='event-signup'),
    path('event/<int:pk>/quit', views.event_quit, name='event-quit'),
]

urlpatterns += [
    path('register/', views.PlayerCreateView.as_view(), name='register'),
    path('setting/', views.PlayerUpdateView.as_view(), name='setting'),
]

urlpatterns += [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
