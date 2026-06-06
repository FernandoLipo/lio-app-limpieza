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

# Importamos el generador de PDF nativo y seguro para Android
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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

            self.lbl_estado = Label(text="Listo para operar.", size_hint_y=None, height=dp(40), color=(1, 1, 0, 1), font_size='15sp', bold=True)
            layout_principal.add_widget(self.lbl_estado)

            layout_principal.add_widget(Widget())

            # Botones inferiores: GUARDAR y EXPORTAR PDF
            layout_botones = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(65), spacing=dp(15))
            
            self.boton_guardar = Button(text="GUARDAR", font_size='18sp', bold=True, background_color=(0.1, 0.5, 0.8, 1))
            self.boton_guardar.bind(on_release=self.guardar_producto)
            layout_botones.add_widget(self.boton_guardar)

            boton_pdf = Button(text="EXPORTAR PDF", font_size='18sp', bold=True, background_color=(0.7, 0.2, 0.2, 1))
            boton_pdf.bind(on_release=self.generar_pdf)
            layout_botones.add_widget(boton_pdf)

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

    def generar_pdf(self, instance):
        try:
            self.cursor.execute("SELECT codigo, nombre, precio FROM productos ORDER BY nombre ASC")
            todos_los_productos = self.cursor.fetchall()

            if not todos_los_productos:
                self.lbl_estado.text = "No hay productos para exportar."
                return

            # Ruta interna de guardado
            ruta_pdf = os.path.join(self.user_data_dir, "Lista_de_Precios.pdf")
            
            # Crear documento PDF basico
            doc = SimpleDocTemplate(ruta_pdf, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Estilos del PDF
            estilo_titulo = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=18, alignment=1, spaceAfter=15)
            estilo_celda = ParagraphStyle('Celda', parent=styles['Normal'], fontSize=10)
            
            story.append(Paragraph("<b>LISTA GENERAL DE PRECIOS - LIO APP</b>", estilo_titulo))
            story.append(Spacer(1, 10))
            
            # Encabezados de la tabla
            tabla_datos = [["CODIGO", "DESCRIPCION", "PRECIO"]]
            
            # Cargar los productos a la tabla del PDF
            for prod in todos_los_productos:
                precio_formateado = f"${prod[2]:,.2f}"
                tabla_datos.append([str(prod[0]), str(prod[1]), precio_formateado])
            
            # Crear y diseñar la tabla
            t = Table(tabla_datos, colWidths=[110, 260, 110])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0D47A1')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('ALIGN', (2,1), (2,-1), 'RIGHT'),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ]))
            
            story.append(t)
            doc.build(story)
            
            self.lbl_estado.text = "PDF creado con exito!"
            
        except Exception as e:
            self.lbl_estado.text = f"Error al crear PDF: {str(e)}"

    def on_stop(self):
        try:
            self.conexion.close()
        except:
            pass

if __name__ == "__main__":
    MiAppEscanner().run()
