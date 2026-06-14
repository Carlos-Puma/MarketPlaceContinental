from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from ecommerce.models import Product
from .forms import SellerForm, UserEditForm, UserForm
from .models import CustomUser, Seller
from .permissions import IsOwnerSellerPermission, IsOwnerUserPermission
from .serializers import CreateSellerSerializer, SellerSerializer, UserCreateSerializer, UserSerializer


class UserCreateAPIView(CreateAPIView):
    serializer_class = UserCreateSerializer


class UserRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all()
    permission_classes = [IsOwnerUserPermission, IsAuthenticated]


class SellerCreateAPIView(CreateAPIView):
    serializer_class = CreateSellerSerializer
    permission_classes = [IsAuthenticated]


class SellerRetirieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = SellerSerializer
    queryset = Seller.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerSellerPermission]


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect(request.GET.get("next") or "home")

        messages.error(request, "Correo o contrasena incorrectos.")

    return render(request, "users/login.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    user_registration = UserForm(request.POST or None)

    if request.method == "POST" and user_registration.is_valid():
        user = user_registration.save()
        login(request, user)
        return redirect("home")

    return render(request, "users/register.html", {"user_registration": user_registration})


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def user_panel_view(request):
    products = Product.objects.none()
    if hasattr(request.user, "seller"):
        products = request.user.seller.products.all()

    return render(request, "users/user_panel.html", {"products": products})


@login_required
def user_edit_view(request):
    user_form = UserEditForm(request.POST or None, instance=request.user)
    seller_form = None

    if hasattr(request.user, "seller"):
        seller_form = SellerForm(request.POST or None, instance=request.user.seller)

    if request.method == "POST" and user_form.is_valid() and (seller_form is None or seller_form.is_valid()):
        user_form.save()
        if seller_form is not None:
            seller_form.save()
        return redirect("users:user_panel")

    return render(request, "users/users_edit.html", {"user_form": user_form, "seller_form": seller_form})


@login_required
def seller_register_view(request):
    if hasattr(request.user, "seller"):
        return redirect("users:user_panel")

    seller_form = SellerForm(request.POST or None)

    if request.method == "POST" and seller_form.is_valid():
        seller = seller_form.save(commit=False)
        seller.profile = request.user
        seller.save()
        return redirect("users:user_panel")

    return render(request, "users/seller_register.html", {"seller_form": seller_form})
