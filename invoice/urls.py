from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("cashcall", views.CashCallViewSet, "cashcall")
router.register("bill", views.BillViewSet, "bill")
router.register("investor", views.InvestorViewSet, "investor")
router.register("investment", views.InvestmentViewSet, "investment")

urlpatterns = [
    path("", include(router.urls)),
    path("generate", views.generate, name="generate"),
    path("validate", views.validate, name="validate"),
    path("send", views.send, name="send"),
]
