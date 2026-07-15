from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("health/ready/", views.readiness, name="readiness"),
    path("auth/csrf/", views.csrf_view, name="auth-csrf"),
    path("diagnosis-config/", views.diagnosis_config, name="diagnosis-config"),
    path("projects/", views.project_list, name="project-list"),
    path("auth/login/", views.login_view, name="auth-login"),
    path("auth/register/", views.register_view, name="auth-register"),
    path("auth/logout/", views.logout_view, name="auth-logout"),
    path("auth/me/", views.me_view, name="auth-me"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/avatar/", views.profile_avatar_view, name="profile-avatar"),
    path("preferences/", views.preference_view, name="preferences"),
    path("uploads/", views.upload_source, name="uploads"),
    path("diagnoses/", views.diagnosis_list, name="diagnosis-list"),
    path("diagnoses/<int:diagnosis_id>/", views.diagnosis_detail, name="diagnosis-detail"),
    path("diagnosis-jobs/", views.diagnosis_job_list, name="diagnosis-job-list"),
    path("diagnosis-jobs/<int:job_id>/", views.diagnosis_job_detail, name="diagnosis-job-detail"),
]
