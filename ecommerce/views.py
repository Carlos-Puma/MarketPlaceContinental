from django.db.models import Q
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from ecommerce.custom_permissions import IsOwnerOrReadOnly, IsStaffOrReadOnly
from ecommerce.filters import ProductFilter
from ecommerce.models import Category, Product
from ecommerce.serializers import CategorySerializer, ProductSerializer


UNICONNET_PAGES = {
    "servicios": {
        "eyebrow": "Servicios",
        "title": "Apoyo academico y servicios especializados",
        "intro": "Estudiantes de ciclos avanzados ofrecen conocimientos, habilidades y soluciones rapidas a otros alumnos de la comunidad universitaria.",
        "items": [
            ("Tutorias de cursos", "Refuerzo para materias complejas, primeros ciclos y preparacion para evaluaciones."),
            ("Ingles, matematicas y programacion", "Clases personalizadas para tareas, proyectos y aprendizaje practico."),
            ("Diseño grafico y edicion", "Piezas visuales, videos, fotografia, logotipos y contenido para trabajos o emprendimientos."),
            ("Reparacion de laptops", "Diagnostico, mantenimiento, instalacion de programas y soporte tecnico accesible."),
            ("CV y emprendimiento", "Asesoria para perfil profesional, pitch, validacion de ideas y primeros pasos comerciales."),
            ("Chat y reputacion", "Comunicacion directa, calificaciones y reseñas para operar con confianza."),
        ],
    },
    "productos": {
        "eyebrow": "Productos",
        "title": "Recursos universitarios reutilizados",
        "intro": "UNICONNET facilita la compra, venta o alquiler de materiales academicos y herramientas de estudio a precios accesibles.",
        "items": [
            ("Libros usados", "Textos universitarios, separatas y resumenes de cursos."),
            ("Calculadoras y herramientas", "Calculadoras cientificas, kits, reglas, materiales y equipos academicos."),
            ("Laptops y tecnologia", "Laptops, cargadores, audifonos, memorias USB y accesorios para estudio."),
            ("Materiales academicos", "Apuntes digitales, impresiones, anillados y recursos organizados."),
            ("Comida y accesorios", "Soluciones practicas para el dia a dia universitario."),
            ("Publicaciones destacadas", "Mayor visibilidad para productos o servicios con alta demanda."),
        ],
    },
    "beneficios": {
        "eyebrow": "Beneficios",
        "title": "Una comunidad que se ayuda y genera valor",
        "intro": "El objetivo es reducir barreras de acceso, crear oportunidades economicas y fortalecer la confianza entre estudiantes.",
        "items": [
            ("Alumnos nuevos", "Reciben apoyo, materiales accesibles y orientacion de estudiantes con experiencia."),
            ("Alumnos avanzados", "Generan ingresos ofreciendo servicios, tutorias o recursos que ya no utilizan."),
            ("Comunidad universitaria", "Impulsa colaboracion, intercambio responsable y cultura de apoyo."),
            ("Menos desperdicio", "Promueve la reutilizacion de libros, apuntes, equipos y materiales."),
            ("Mas confianza", "Perfiles, reseñas, reportes y comunicacion directa reducen riesgos."),
            ("Mejor acceso", "Centraliza recursos y oportunidades dentro de una plataforma organizada."),
        ],
    },
    "modelo": {
        "eyebrow": "Modelo de ingreso",
        "title": "Sostenible desde la participacion estudiantil",
        "intro": "La plataforma puede sostenerse con ingresos proporcionales al valor que genera para vendedores, prestadores y compradores.",
        "items": [
            ("Comision por venta", "Una comision pequena por transaccion o servicio concretado."),
            ("Publicaciones destacadas", "Anuncios con mayor visibilidad dentro de categorias y busquedas."),
            ("Membresias premium", "Beneficios para usuarios frecuentes o vendedores con mayor volumen."),
            ("Validacion inicial", "Empieza con una comunidad universitaria antes de escalar."),
            ("Alianzas", "Convenios con centros de estudiantes, facultades o emprendimientos."),
            ("Crecimiento gradual", "Escala por carrera, facultad, sede y universidad."),
        ],
    },
    "crecimiento": {
        "eyebrow": "Escala",
        "title": "De una universidad a muchas",
        "intro": "UNICONNET empieza resolviendo necesidades concretas en una universidad y luego replica el modelo en nuevas sedes e instituciones.",
        "items": [
            ("Fase 1: comunidad local", "Validar necesidades, categorias y comportamiento de usuarios."),
            ("Fase 2: confianza", "Mejorar reputacion, moderacion, reportes y verificacion."),
            ("Fase 3: expansion", "Abrir nuevas carreras, facultades y sedes."),
            ("Fase 4: red universitaria", "Conectar comunidades de distintas universidades."),
            ("Marketing estudiantil", "Difusion en redes sociales, grupos universitarios y referidos."),
            ("Producto escalable", "Una estructura digital replicable y adaptable."),
        ],
    },
}


def home(request):
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "").strip()

    products = Product.objects.select_related("category").prefetch_related("product_images").order_by("-id")
    categories = Category.objects.prefetch_related("products").order_by("title")

    if query:
        products = products.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(category__title__icontains=query)
        )

    if selected_category:
        products = products.filter(category__slug=selected_category)

    return render(
        request,
        "ecommerce/home.html",
        {
            "products": products,
            "categories": categories,
            "query": query,
            "selected_category": selected_category,
        },
    )


def uniconnet_page(request, page_slug):
    page = UNICONNET_PAGES[page_slug]
    return render(request, "ecommerce/info_page.html", {"page": page, "page_slug": page_slug})


class APIRootView(APIView):
    def get(self, request):
        data = {
            "ecommerce": reverse("ecommerce:product-list", request=request),
            "category": reverse("ecommerce:category-list", request=request),
        }
        return Response(data)


class ProductList(ListCreateAPIView):
    queryset = Product.objects.all().order_by("id")
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["title", "description", "category__title"]
    ordering_fields = ["price", "stock", "category"]


class ProductDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    lookup_field = "slug"
    permission_classes = [IsOwnerOrReadOnly]


class CategoryList(ListCreateAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all().order_by("id")
    permission_classes = [IsStaffOrReadOnly]


class CategoryDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
    lookup_field = "slug"
    permission_classes = [IsStaffOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.products.count() > 0:
            return Response({"error": "La colección no se puede eliminar porque tiene productos"})
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
