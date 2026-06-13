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
    ("Tecnologia", "#111111", [
        ("Audifonos Bluetooth Continental", "Audifonos inalambricos con estuche compacto y sonido nitido.", 129, 18),
        ("Mouse ergonomico inalambrico", "Mouse recargable para clases, oficina y gaming casual.", 75, 25),
        ("Teclado mecanico compacto", "Teclado 65% con iluminacion suave y switches tactiles.", 169, 10),
        ("Power bank 20000 mAh", "Bateria portatil de alta capacidad para jornadas largas.", 119, 14),
        ("Soporte para laptop aluminio", "Base plegable para estudiar con mejor postura.", 95, 12),
        ("Parlante Bluetooth mini", "Parlante portatil con graves solidos y diseno minimalista.", 89, 20),
    ]),
    ("Moda", "#7a604c", [
        ("Mochila universitaria azul", "Mochila resistente con compartimento para laptop.", 89, 30),
        ("Casaca urbana gris", "Casaca ligera para uso diario con acabado moderno.", 159, 9),
        ("Polo Continental basico", "Polo de algodon suave con corte casual universitario.", 55, 40),
        ("Zapatillas urbanas blancas", "Zapatillas comodas para caminar por campus y ciudad.", 185, 8),
        ("Gorra minimal azul", "Gorra ajustable con estilo limpio y combinable.", 58, 22),
        ("Bolso tote canvas", "Bolso reutilizable para libros, laptop y compras pequenas.", 65, 16),
    ]),
    ("Libros y Papeleria", "#3a2d25", [
        ("Cuaderno premium A5", "Cuaderno de tapa dura con hojas punteadas.", 55, 35),
        ("Pack lapiceros gel", "Set de lapiceros de escritura suave en colores variados.", 52, 28),
        ("Planner academico 2026", "Agenda semanal para organizar entregas, cursos y examenes.", 70, 18),
        ("Libro emprendimiento universitario", "Guia practica para validar ideas y lanzar proyectos.", 80, 11),
        ("Archivador ejecutivo gris", "Archivador resistente para documentos y separadores.", 60, 19),
        ("Set resaltadores pastel", "Marcadores de tonos suaves para apuntes limpios.", 50, 32),
    ]),
    ("Hogar", "#9a7b5f", [
        ("Lampara de escritorio LED", "Lampara regulable con luz fria, calida y neutra.", 75, 17),
        ("Taza termica Continental", "Taza con tapa para cafe, infusiones o bebidas frias.", 62, 24),
        ("Organizador de escritorio", "Base modular para lapices, notas y accesorios.", 68, 15),
        ("Difusor aromatico USB", "Difusor compacto para escritorio o habitacion.", 92, 12),
        ("Botella deportiva acero", "Botella reutilizable con aislamiento termico.", 85, 20),
        ("Mini ventilador recargable", "Ventilador portatil con base para escritorio.", 78, 13),
    ]),
    ("Deportes", "#5f4b3c", [
        ("Tomatodo deportivo 1L", "Botella resistente con medidor y tapa segura.", 58, 26),
        ("Mat de yoga antideslizante", "Colchoneta ligera para entrenamiento y estiramiento.", 95, 10),
        ("Liga de resistencia set", "Set de ligas para rutinas de fuerza y movilidad.", 72, 16),
        ("Balon de futsal", "Balon resistente para partidos recreativos.", 99, 9),
        ("Toalla deportiva microfibra", "Toalla compacta de secado rapido.", 52, 25),
        ("Maletin deportivo gris", "Bolso amplio para gimnasio, cancha o viajes cortos.", 135, 7),
    ]),
    ("Accesorios", "#1f1f1f", [
        ("Cable USB-C reforzado", "Cable trenzado de carga rapida y alta durabilidad.", 50, 45),
        ("Funda laptop 15 pulgadas", "Funda acolchada con bolsillo frontal.", 69, 21),
        ("Holder magnetico celular", "Soporte magnetico para escritorio o auto.", 57, 19),
        ("Llavero multitool", "Accesorio compacto con herramientas de uso diario.", 54, 30),
        ("Organizador de cables", "Set de clips y correas para escritorio ordenado.", 50, 34),
        ("Tarjetero minimalista", "Tarjetero delgado con acabado sobrio.", 59, 18),
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
        navy = "#0b2545"
        soft_gray = "#d8e0ea"
        white = "#ffffff"

        draw.rounded_rectangle((70, 70, 1130, 830), radius=44, fill=white, outline=soft_gray, width=3)
        draw.rounded_rectangle((70, 70, 1130, 275), radius=44, fill=accent)
        draw.rectangle((70, 180, 1130, 275), fill=accent)

        draw.ellipse((820, 155, 1050, 385), fill="#ffffff33")
        draw.ellipse((745, 230, 965, 450), fill="#ffffff22")
        draw.rounded_rectangle((145, 350, 1055, 690), radius=34, fill="#eef4fb", outline="#d3deeb", width=2)

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
