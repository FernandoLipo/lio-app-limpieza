from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.metrics import dp
import sqlite3
import os

# Importamos las herramientas de Pillow para dibujar la lista de precios
from PIL import Image, ImageDraw, ImageFont

class MiAppEscanner(App):
    def build(self):
        try:
            ruta_app = self.user_data_dir
            self.base_datos = os.path.join(ruta_app, "precios.db")
            
            self.conexion = sqlite3.connect(self.base_datos)
            self.cursor = self.conexion.cursor()
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    codigo TEXT PRIMARY KEY,
                    nombre TEXT,
                    precio REAL
                )
            """)
            self.conexion.commit()

            layout_principal = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
            
            layout_principal.add_widget(Label(
                text="LIO APP", 
                size_hint_y=None, 
                height=dp(40), 
                font_size='26sp', 
                bold=True
            ))
            
            layout_principal.add_widget(Label(
                text="Control de Articulos de Limpieza", 
                size_hint_y=None, 
                height=dp(20), 
                font_size='14sp',
                color=(0.7, 0.7, 0.7, 1)
            ))

            layout_formulario = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None)
            layout_formulario.bind(minimum_height=layout_formulario.setter('height'))

            layout_formulario.add_widget(Label(text="Codigo de Barras:", size_hint_y=None, height=dp(25), font_size='16sp', bold=True))
            # Campo numerico puro para usar con teclado o lector de mano externo
            self.input_codigo = TextInput(text="", multiline=False, size_hint_y=None, height=dp(55), font_size='20sp', input_type='number')
            self.input_codigo.bind(on_text_validate=self.buscar_producto)
            layout_formulario.add_widget(self.input_codigo)

            boton_buscar_manual = Button(text="BUSCAR CODIGO", size_hint_y=None, height=dp(50), font_size='16sp', bold=True, background_color=(0.1, 0.6, 0.3, 1))
            boton_buscar_manual.bind(on_release=self.buscar_producto)
            layout_formulario.add_widget(boton_buscar_manual)

            layout_formulario.add_widget(Label(text="Descripcion del Producto:", size_hint_y=None, height=dp(25), font_size='16sp', bold=True))
            self.input_nombre = TextInput(multiline=False, size_hint_y=None, height=dp(55), font_size='18sp')
            layout_formulario.add_widget(self.input_nombre)

            layout_formulario.add_widget(Label(text="Precio ($):", size_hint_y=None, height=dp(25), font_size='16sp', bold=True))
            self.input_precio = TextInput(multiline=False, size_hint_y=None, height=dp(55), font_size='18sp', input_type='number')
            layout_formulario.add_widget(self.input_precio)

            layout_principal.add_widget(layout_formulario)

            self.lbl_estado = Label(text="Listo para operar (Sin camara).", size_hint_y=None, height=dp(40), color=(1, 1, 0, 1), font_size='15sp', bold=True)
            layout_principal.add_widget(self.lbl_estado)

            layout_principal.add_widget(Widget())

            # Botones inferiores de accion rapida
            layout_botones = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(65), spacing=dp(15))
            
            self.boton_guardar = Button(text="GUARDAR", font_size='18sp', bold=True, background_color=(0.1, 0.5, 0.8, 1))
            self.boton_guardar.bind(on_release=self.guardar_producto)
            layout_botones.add_widget(self.boton_guardar)

            boton_imagen = Button(text="EXPORTAR IMAGEN", font_size='18sp', bold=True, background_color=(0.7, 0.2, 0.2, 1))
            boton_imagen.bind(on_release=self.generar_imagen_precios)
            layout_botones.add_widget(boton_imagen)

            layout_principal.add_widget(layout_botones)
            return layout_principal

        except Exception as e:
            layout_error = BoxLayout(orientation='vertical', padding=dp(20))
            layout_error.add_widget(Label(text="ERROR INTERNO:", size_hint_y=None, height=dp(40), color=(1,0,0,1)))
            return layout_error

    def buscar_producto(self, instance):
        codigo = self.input_codigo.text.strip()
        if not codigo:
            self.lbl_estado.text = "Por favor, escriba o escanee un codigo."
            return
        self.cursor.execute("SELECT nombre, precio FROM productos WHERE codigo = ?", (codigo,))
        resultado = self.cursor.fetchone()
        if resultado:
            nombre, precio = resultado
            self.input_nombre.text = nombre
            self.input_precio.text = str(precio)
            self.lbl_estado.text = f"Producto {codigo} encontrado."
        else:
            self.input_nombre.text = ""
            self.input_precio.text = ""
            self.lbl_estado.text = "Codigo NUEVO. Ingrese datos y guarde."

    def guardar_producto(self, instance):
        codigo = self.input_codigo.text.strip()
        nombre = self.input_nombre.text.strip()
        precio_texto = self.input_precio.text.strip()

        if not codigo or not nombre or not precio_texto:
            self.lbl_estado.text = "Error: Campos vacios."
            return
        try:
            precio = float(precio_texto)
        except ValueError:
            self.lbl_estado.text = "Error: El precio debe ser un numero."
            return

        self.cursor.execute("INSERT OR REPLACE INTO productos VALUES (?, ?, ?)", (codigo, nombre, precio))
        self.conexion.commit()
        self.lbl_estado.text = f"Producto {codigo} guardado!"

    def generar_imagen_precios(self, instance):
        try:
            self.cursor.execute("SELECT codigo, nombre, precio FROM productos ORDER BY nombre ASC")
            todos_los_productos = self.cursor.fetchall()

            if not todos_los_productos:
                self.lbl_estado.text = "No hay productos para exportar."
                return

            # Configuracion de dimensiones de la imagen liquida
            ancho_imagen = 800
            alto_encabezado = 120
            alto_fila = 40
            alto_imagen = alto_encabezado + (len(todos_los_productos) * alto_fila) + 40

            # Crear lienzo en blanco
            imagen = Image.new("RGB", (ancho_imagen, alto_imagen), "white")
            dibujo = ImageDraw.Draw(imagen)

            # Fuentes estandar del sistema
            try:
                fuente_titulo = ImageFont.load_default()
                fuente_texto = ImageFont.load_default()
            except:
                fuente_titulo = None
                fuente_texto = None

            # Dibujar Titulo Principal
            dibujo.rectangle([(0, 0), (ancho_imagen, 70)], fill="#0D47A1")
            dibujo.text((20, 20), "LISTA GENERAL DE PRECIOS - LIO APP", fill="white", font=fuente_titulo)

            # Dibujar Encabezados de Tabla
            dibujo.rectangle([(0, 70), (ancho_imagen, alto_encabezado)], fill="#1565C0")
            dibujo.text((20, 85), "CODIGO DE BARRAS", fill="white", font=fuente_texto)
            dibujo.text((280, 85), "DESCRIPCION DEL ARTICULO", fill="white", font=fuente_texto)
            dibujo.text((660, 85), "PRECIO", fill="white", font=fuente_texto)

            # Dibujar las filas de productos dinamicamente
            y_actual = alto_encabezado
            for i, prod in enumerate(todos_los_productos):
                # Color de fondo intercalado para facilitar la lectura
                color_fondo = "#F5F5F5" if i % 2 == 0 else "#FFFFFF"
                dibujo.rectangle([(0, y_actual), (ancho_imagen, y_actual + alto_fila)], fill=color_fondo)

                precio_formateado = f"${prod[2]:,.2f}"
                
                # Escribir los datos en sus columnas correspondientes
                dibujo.text((20, y_actual + 12), str(prod[0]), fill="black", font=fuente_texto)
                dibujo.text((280, y_actual + 12), str(prod[1]), fill="black", font=fuente_texto)
                dibujo.text((660, y_actual + 12), precio_formateado, fill="black", font=fuente_texto)

                # Linea divisoria gris tenue
                dibujo.line([(0, y_actual + alto_fila), (ancho_imagen, y_actual + alto_fila)], fill="#E0E0E0", width=1)
                y_actual += alto_fila

            # Guardar la imagen final en el almacenamiento de la app
            ruta_imagen = os.path.join(self.user_data_dir, "Lista_de_Precios.png")
            imagen.save(ruta_imagen)
            
            self.lbl_estado.text = "Foto de precios creada con exito!"
            
        except Exception as e:
            self.lbl_estado.text = f"Error al crear foto: {str(e)}"

    def on_stop(self):
        try:
            self.conexion.close()
        except:
            pass

if __name__ == "__main__":
    MiAppEscanner().run()
