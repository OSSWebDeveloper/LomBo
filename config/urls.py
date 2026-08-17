from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from accounts import views as acc
from accounts.forms import SaytKirishFormasi
from contracts import views as con

admin.site.site_header = 'Lombard — boshqaruv paneli'
admin.site.site_title = 'Lombard admin'
admin.site.index_title = 'Boshqaruv'

urlpatterns = [
    path('admin/', admin.site.urls),

    # Ichki xizmat — manzili settings.PANEL_PATH da (kodda ochiq turmaydi,
    # LOMBARD_PANEL_PATH muhit o'zgaruvchisidan olinadi).
    path(f'{settings.PANEL_PATH}/', include('panel.urls')),

    path('kirish/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=SaytKirishFormasi,
        redirect_authenticated_user=False), name='login'),
    path('chiqish/', auth_views.LogoutView.as_view(), name='logout'),

    path('', con.dashboard, name='dashboard'),

    # Shartnomalar
    path('shartnomalar/', con.contract_list, name='contract_list'),
    path('shartnoma/yangi/', con.contract_create, name='contract_create'),
    path('shartnoma/<int:pk>/', con.contract_detail, name='contract_detail'),
    path('shartnoma/<int:pk>/tahrir/', con.contract_edit, name='contract_edit'),
    path('shartnoma/<int:pk>/yuklab-olish/', con.contract_download, name='contract_download'),
    path('shartnoma/<int:pk>/pdf/', con.contract_download_pdf, name='contract_download_pdf'),
    path('shartnoma/<int:pk>/garov/', con.contract_download_garov, name='contract_download_garov'),
    path('shartnoma/<int:pk>/garov-pdf/', con.contract_download_garov_pdf, name='contract_download_garov_pdf'),
    path('shartnoma/<int:pk>/ochirish/', con.contract_delete, name='contract_delete'),

    # O'chirish so'rovlari
    path('sorovlar/', con.delete_requests, name='delete_requests'),
    path('sorov/<int:pk>/<str:action>/', con.delete_request_decide,
         name='delete_request_decide'),

    # Shablonlar (maxsus vakolatli boshliq)
    path('shablonlar/', con.shablon_list, name='shablon_list'),
    path('shablon/<str:turi>/', con.shablon_edit, name='shablon_edit'),
    path('shablon/<str:turi>/yuklab-olish/', con.shablon_download, name='shablon_download'),
    path('shablon/<str:turi>/almashtirish/', con.shablon_upload, name='shablon_upload'),

    # Monitoring va tarix
    path('monitoring/', con.monitoring, name='monitoring'),
    path('tarix/', con.amallar, name='amallar'),

    # Ishchilar
    path('ishchilar/', acc.worker_list, name='worker_list'),
    path('ishchi/yangi/', acc.worker_create, name='worker_create'),
    path('ishchi/<int:pk>/', acc.worker_detail, name='worker_detail'),
    path('ishchi/<int:pk>/tahrir/', acc.worker_edit, name='worker_edit'),
    path('ishchi/<int:pk>/parol/', acc.worker_password, name='worker_password'),
    path('ishchi/<int:pk>/boshatish/', acc.worker_fire, name='worker_fire'),
]

# Garov suratlari. DEBUG rejimida Django o'zi beradi; serverda esa
# PythonAnywhere'ning Web bo'limida /media/ uchun statik yo'l ko'rsatiladi.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
