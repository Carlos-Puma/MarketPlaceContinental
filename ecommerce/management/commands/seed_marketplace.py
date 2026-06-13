from io import BytesIO
from textwrap import wrap

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

LEGACY_DEMO_CATEGORIES = [
    "Tecnologia",
    "Moda",
    "Libros",
    "Libros y Papeleria",
    "Hogar",
    "Deportes",
    "Accesorios",
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
            demo_categories = [category_title for category_title, _, _ in CATALOG] + LEGACY_DEMO_CATEGORIES
            Image.objects.filter(product__category__title__in=demo_categories).delete()
            Product.objects.filter(category__title__in=demo_categories).delete()
            Category.objects.filter(title__in=LEGACY_DEMO_CATEGORIES).delete()

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

        self.draw_matching_icon(draw, title, category, accent)

        y = 715
        for line in wrap(title, width=28)[:2]:
            draw.text((130, y), line, fill=navy, font=title_font)
            y += 58

        price_text = f"S/ {price}"
        bbox = draw.textbbox((0, 0), price_text, font=price_font)
        draw.text((1090 - (bbox[2] - bbox[0]), 720), price_text, fill=accent, font=price_font)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def initials(self, title):
        words = [word[0] for word in title.split() if word]
        return "".join(words[:2]).upper()

    def draw_matching_icon(self, draw, title, category, accent):
        text = f"{title} {category}".lower()
        center_x, center_y = 600, 520
        dark = "#111111"
        beige = "#eadfce"
        muted = "#7a604c"

        if any(word in text for word in ["tutoria", "clase", "matematica", "programacion", "calculo", "ingles"]):
            self.draw_board(draw, center_x, center_y, accent, dark)
        elif any(word in text for word in ["diseno", "edicion", "fotografia", "logotipo"]):
            self.draw_palette(draw, center_x, center_y, accent, dark)
        elif any(word in text for word in ["laptop", "revision", "instalacion", "formateo", "mantenimiento", "cargador"]):
            self.draw_laptop(draw, center_x, center_y, accent, dark)
        elif any(word in text for word in ["cv", "linkedin", "emprendimiento", "pitch"]):
            self.draw_document(draw, center_x, center_y, accent, dark)
        elif any(word in text for word in ["libro", "apuntes", "separatas"]):
            self.draw_books(draw, center_x, center_y, accent, dark)
        elif "calculadora" in text:
            self.draw_calculator(draw, center_x, center_y, accent, dark)
        elif "audifonos" in text:
            self.draw_headphones(draw, center_x, center_y, accent, dark)
        elif "snack" in text:
            self.draw_snack(draw, center_x, center_y, accent, dark, beige, muted)
        else:
            draw.ellipse((center_x - 105, center_y - 105, center_x + 105, center_y + 105), fill=accent)
            draw.text((center_x - 52, center_y - 38), self.initials(title), fill="#ffffff", font=ImageFont.load_default())

    def draw_board(self, draw, x, y, accent, dark):
        draw.rounded_rectangle((x - 190, y - 115, x + 190, y + 90), radius=18, fill=dark)
        draw.rectangle((x - 160, y - 85, x + 160, y + 45), fill="#ffffff")
        draw.line((x - 135, y - 45, x - 45, y - 45), fill=accent, width=8)
        draw.line((x - 135, y - 5, x + 80, y - 5), fill=accent, width=8)
        draw.line((x - 80, y + 38, x + 130, y + 38), fill=accent, width=8)
        draw.rectangle((x - 30, y + 90, x + 30, y + 130), fill=dark)
        draw.rounded_rectangle((x - 110, y + 130, x + 110, y + 150), radius=10, fill=dark)

    def draw_palette(self, draw, x, y, accent, dark):
        draw.ellipse((x - 150, y - 125, x + 150, y + 125), fill=accent)
        draw.ellipse((x + 35, y - 15, x + 95, y + 45), fill="#ffffff")
        for dx, dy, color in [(-70, -55, dark), (-20, -80, "#ffffff"), (-85, 25, "#eadfce"), (-20, 45, dark)]:
            draw.ellipse((x + dx - 20, y + dy - 20, x + dx + 20, y + dy + 20), fill=color)
        draw.rounded_rectangle((x + 105, y + 35, x + 180, y + 55), radius=10, fill=dark)

    def draw_laptop(self, draw, x, y, accent, dark):
        draw.rounded_rectangle((x - 170, y - 105, x + 170, y + 90), radius=20, fill=dark)
        draw.rectangle((x - 140, y - 75, x + 140, y + 60), fill="#ffffff")
        draw.line((x - 95, y - 30, x + 65, y - 30), fill=accent, width=8)
        draw.line((x - 95, y + 10, x + 110, y + 10), fill=accent, width=8)
        draw.rounded_rectangle((x - 215, y + 95, x + 215, y + 135), radius=14, fill=accent)
        draw.arc((x + 95, y - 115, x + 190, y - 20), 210, 35, fill=accent, width=12)

    def draw_document(self, draw, x, y, accent, dark):
        draw.rounded_rectangle((x - 115, y - 145, x + 115, y + 145), radius=18, fill="#ffffff", outline=dark, width=8)
        draw.rectangle((x - 65, y - 100, x + 65, y - 50), fill=accent)
        draw.line((x - 70, y - 5, x + 70, y - 5), fill=dark, width=8)
        draw.line((x - 70, y + 35, x + 70, y + 35), fill=dark, width=8)
        draw.line((x - 70, y + 75, x + 35, y + 75), fill=dark, width=8)

    def draw_books(self, draw, x, y, accent, dark):
        draw.rounded_rectangle((x - 155, y - 95, x - 25, y + 125), radius=14, fill=accent)
        draw.rounded_rectangle((x - 15, y - 115, x + 125, y + 105), radius=14, fill=dark)
        draw.rounded_rectangle((x + 65, y - 75, x + 185, y + 135), radius=14, fill="#ffffff", outline=dark, width=6)
        draw.line((x - 120, y - 40, x - 55, y - 40), fill="#ffffff", width=7)
        draw.line((x + 5, y - 55, x + 90, y - 55), fill="#ffffff", width=7)
        draw.line((x + 95, y - 15, x + 155, y - 15), fill=accent, width=7)

    def draw_calculator(self, draw, x, y, accent, dark):
        draw.rounded_rectangle((x - 115, y - 145, x + 115, y + 145), radius=22, fill=dark)
        draw.rounded_rectangle((x - 80, y - 105, x + 80, y - 55), radius=10, fill="#ffffff")
        for row in range(3):
            for col in range(3):
                x0 = x - 75 + col * 55
                y0 = y - 20 + row * 48
                draw.rounded_rectangle((x0, y0, x0 + 34, y0 + 30), radius=7, fill=accent if row == 2 else "#ffffff")

    def draw_headphones(self, draw, x, y, accent, dark):
        draw.arc((x - 145, y - 145, x + 145, y + 145), 200, 340, fill=dark, width=24)
        draw.rounded_rectangle((x - 155, y - 5, x - 95, y + 105), radius=18, fill=accent)
        draw.rounded_rectangle((x + 95, y - 5, x + 155, y + 105), radius=18, fill=accent)
        draw.line((x - 55, y + 115, x + 55, y + 115), fill=dark, width=12)

    def draw_snack(self, draw, x, y, accent, dark, beige, muted):
        draw.rounded_rectangle((x - 120, y - 130, x + 120, y + 130), radius=28, fill=accent)
        draw.polygon([(x - 120, y - 130), (x + 120, y - 130), (x + 85, y - 70), (x - 85, y - 70)], fill=dark)
        draw.ellipse((x - 55, y - 30, x + 55, y + 80), fill=beige)
        draw.line((x - 55, y + 100, x + 55, y + 100), fill=muted, width=12)
