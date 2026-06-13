from pathlib import Path
from textwrap import wrap

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

from ecommerce.models import Category, Image, Product


CATALOG = [
    ("Tutorias y clases", "#111111", [
        ("Tutoria de calculo I", "Refuerzo para limites, derivadas e integrales con estudiante de ciclos avanzados.", 35, 12),
        ("Clase de programacion Python", "Acompañamiento practico para tareas, proyectos y fundamentos de programacion.", 45, 10),
        ("Asesoria de matematica basica", "Sesiones para estudiantes de primeros ciclos que necesitan nivelacion.", 30, 15),
        ("Clase de ingles conversacional", "Practica guiada para exposiciones, entrevistas y trabajos universitarios.", 40, 8),
    ]),
    ("Servicios creativos", "#6f5744", [
        ("Diseno grafico para exposiciones", "Diapositivas, afiches y piezas visuales con estilo profesional.", 55, 9),
        ("Edicion de video academico", "Edicion de videos para proyectos, sustentaciones y redes estudiantiles.", 70, 7),
        ("Creacion de logotipo", "Identidad visual para emprendimientos universitarios y proyectos de clase.", 85, 6),
        ("Fotografia para perfil profesional", "Sesion rapida para CV, LinkedIn o portafolio.", 60, 5),
    ]),
    ("Soporte tecnologico", "#2a211b", [
        ("Revision de laptop", "Diagnostico de rendimiento, limpieza de software y recomendaciones de mejora.", 50, 10),
        ("Instalacion de programas", "Apoyo para instalar herramientas academicas, IDEs y software de clase.", 35, 14),
        ("Formateo y respaldo basico", "Servicio coordinado con copia de archivos y reinstalacion limpia.", 90, 5),
        ("Mantenimiento preventivo", "Limpieza y optimizacion para equipos de uso universitario.", 75, 8),
    ]),
    ("CV y emprendimiento", "#9a7b5f", [
        ("Revision de CV universitario", "Mejora de estructura, redaccion y presentacion para practicas.", 45, 12),
        ("Perfil LinkedIn inicial", "Configuracion de perfil profesional y recomendaciones de visibilidad.", 55, 10),
        ("Asesoria de emprendimiento", "Validacion de idea, propuesta de valor y primeros pasos comerciales.", 65, 8),
        ("Pitch para proyecto", "Guion y estructura para presentar una idea de negocio o investigacion.", 60, 7),
    ]),
    ("Material academico", "#3a2d25", [
        ("Libro usado de embriologia", "Libro academico en buen estado para estudiantes de ciencias de la salud.", 80, 3),
        ("Calculadora cientifica", "Calculadora funcional para cursos de matematica, fisica y estadistica.", 65, 4),
        ("Apuntes digitales organizados", "Resumenes y separatas de cursos generales con estructura clara.", 25, 20),
        ("Separatas impresas", "Material fisico de apoyo para repasar antes de examenes.", 20, 18),
    ]),
    ("Productos universitarios", "#1f1f1f", [
        ("Laptop para estudiante", "Equipo de segunda mano ideal para trabajos, clases virtuales y programacion basica.", 950, 2),
        ("Audifonos para clases", "Audifonos funcionales para reuniones, clases y estudio en biblioteca.", 45, 6),
        ("Cargador universal laptop", "Cargador compatible con varios modelos, previa verificacion.", 75, 4),
        ("Snack box universitario", "Combo de comida rapida para jornadas largas de estudio.", 18, 25),
    ]),
]


class Command(BaseCommand):
    help = "Carga categorias, productos e imagenes demo para UNICONNET."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear-demo",
            action="store_true",
            help="Elimina productos demo existentes antes de volver a crearlos.",
        )

    def handle(self, *args, **options):
        if options["clear_demo"]:
            demo_titles = [item[0] for _, _, products in CATALOG for item in products]
            Image.objects.filter(product__title__in=demo_titles).delete()
            Product.objects.filter(title__in=demo_titles).delete()

        created_products = 0
        updated_products = 0
        created_images = 0

        for category_title, color, products in CATALOG:
            category, _ = Category.objects.get_or_create(title=category_title)

            for title, description, price, stock in products:
                product, created = Product.objects.update_or_create(
                    title=title,
                    defaults={
                        "category": category,
                        "description": description,
                        "price": price,
                        "stock": stock,
                    },
                )

                if created:
                    created_products += 1
                else:
                    updated_products += 1

                if not product.product_images.exists():
                    image_bytes = self.build_product_image(title, category_title, price, color)
                    image = Image(product=product)
                    filename = f"demo/{slugify(title)}.png"
                    image.image_location.save(filename, ContentFile(image_bytes), save=True)
                    created_images += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Catalogo listo: {created_products} productos nuevos, "
                f"{updated_products} actualizados, {created_images} imagenes creadas."
            )
        )

    def build_product_image(self, title, category, price, color):
        width, height = 1200, 900
        image = PILImage.new("RGB", (width, height), "#f5f7fb")
        draw = ImageDraw.Draw(image)

        accent = color
        navy = "#111111"
        soft_gray = "#d9c8b7"
        white = "#ffffff"

        draw.rounded_rectangle((70, 70, 1130, 830), radius=44, fill="#eadfce", outline=soft_gray, width=3)
        draw.rounded_rectangle((70, 70, 1130, 275), radius=44, fill=accent)
        draw.rectangle((70, 180, 1130, 275), fill=accent)

        draw.ellipse((820, 155, 1050, 385), fill="#ffffff33")
        draw.ellipse((745, 230, 965, 450), fill="#ffffff22")
        draw.rounded_rectangle((145, 350, 1055, 690), radius=34, fill="#ffffff", outline="#d9c8b7", width=2)

        try:
            title_font = ImageFont.truetype("arialbd.ttf", 54)
            category_font = ImageFont.truetype("arial.ttf", 30)
            price_font = ImageFont.truetype("arialbd.ttf", 58)
            brand_font = ImageFont.truetype("arialbd.ttf", 34)
        except OSError:
            title_font = ImageFont.load_default()
            category_font = ImageFont.load_default()
            price_font = ImageFont.load_default()
            brand_font = ImageFont.load_default()

        draw.text((130, 115), "UNICONNET", fill=white, font=brand_font)
        draw.rounded_rectangle((130, 215, 420, 260), radius=18, fill="#ffffff")
        draw.text((155, 224), category.upper(), fill=accent, font=category_font)

        icon_center = (600, 505)
        draw.ellipse((icon_center[0] - 95, icon_center[1] - 95, icon_center[0] + 95, icon_center[1] + 95), fill=accent)
        draw.text((icon_center[0] - 48, icon_center[1] - 38), self.initials(title), fill=white, font=price_font)

        y = 715
        for line in wrap(title, width=28)[:2]:
            draw.text((130, y), line, fill=navy, font=title_font)
            y += 58

        price_text = f"S/ {price}"
        bbox = draw.textbbox((0, 0), price_text, font=price_font)
        draw.text((1090 - (bbox[2] - bbox[0]), 720), price_text, fill=accent, font=price_font)

        out_dir = Path(settings.MEDIA_ROOT) / "products" / "demo"
        out_dir.mkdir(parents=True, exist_ok=True)
        temp_path = out_dir / "_tmp_product.png"
        image.save(temp_path, format="PNG")
        data = temp_path.read_bytes()
        temp_path.unlink(missing_ok=True)
        return data

    def initials(self, title):
        words = [word[0] for word in title.split() if word]
        return "".join(words[:2]).upper()
