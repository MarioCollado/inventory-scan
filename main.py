import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import requests
import cv2
from pyzbar import pyzbar
from PIL import Image, ImageTk, ImageDraw, ImageFont
import csv
import json
from datetime import datetime
from tkinter import messagebox, filedialog
import os

class InventarioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventario de Alimentos")
        self.root.state('zoomed')
        
        # Configuración inicial
        self.style = ttk.Style(theme='darkly')
        self.inventario = {}
        self.cantidad_var = tk.IntVar(value=1)
        self.cap = None
        self.preview_active = False
        self.archivo_inventario = "inventario.json"
        
        # Cargar inventario si existe
        self.cargar_inventario()
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Configurar cierre seguro
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)

    def crear_interfaz(self):
        """Crea todos los componentes de la interfaz gráfica"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo (controles)
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        
        # Panel derecho (cámara)
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=RIGHT, fill=BOTH, padx=5)
        
        # Tarjeta de búsqueda
        search_card = ttk.Labelframe(left_panel, text="🔍 Buscar Producto", bootstyle=INFO)
        search_card.pack(fill=X, pady=(0, 10))
        
        self.entry_buscar = ttk.Entry(search_card)
        self.entry_buscar.pack(fill=X, padx=5, pady=5)
        self.entry_buscar.bind('<KeyRelease>', self.buscar_producto)
        
        # Tarjeta de registro
        register_card = ttk.Labelframe(left_panel, text="📝 Registrar Producto", bootstyle=PRIMARY)
        register_card.pack(fill=BOTH, expand=True, pady=5)
        
        # Formulario de registro
        self.crear_formulario_registro(register_card)
        
        # Tarjeta de inventario
        inventory_card = ttk.Labelframe(left_panel, text="📦 Inventario", bootstyle=SUCCESS)
        inventory_card.pack(fill=BOTH, expand=True, pady=10)
        
        # Treeview para mostrar inventario
        self.crear_treeview_inventario(inventory_card)
        
        # Botones de acciones
        self.crear_botones_accion(left_panel)
        
        # Vista previa de cámara
        self.crear_vista_camara(right_panel)
        
        # Configurar pesos para expansión
        self.configurar_geometria()

    def crear_formulario_registro(self, parent):
        """Crea el formulario para registrar productos"""
        # Código de barras
        ttk.Label(parent, text="Código de barras:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.entry_codigo = ttk.Entry(parent)
        self.entry_codigo.grid(row=0, column=1, padx=5, pady=5, sticky=EW)
        
        # Nombre del producto
        ttk.Label(parent, text="Nombre del producto*:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        self.entry_nombre = ttk.Entry(parent)
        self.entry_nombre.grid(row=1, column=1, padx=5, pady=5, sticky=EW)
        
        # Cantidad
        ttk.Label(parent, text="Cantidad*:").grid(row=2, column=0, padx=5, pady=5, sticky=W)
        frame_cantidad = ttk.Frame(parent)
        frame_cantidad.grid(row=2, column=1, padx=5, pady=5, sticky=W)
        
        ttk.Button(frame_cantidad, text="-", command=self.decrementar_cantidad, 
                  bootstyle=(OUTLINE, SECONDARY), width=3).pack(side=LEFT, padx=2)
        ttk.Entry(frame_cantidad, textvariable=self.cantidad_var, width=5, 
                 justify='center').pack(side=LEFT, padx=2)
        ttk.Button(frame_cantidad, text="+", command=self.incrementar_cantidad, 
                  bootstyle=(OUTLINE, SECONDARY), width=3).pack(side=LEFT, padx=2)
        
        # Botones de acción
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="➕ Agregar/Actualizar", command=self.agregar_producto, 
                  bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        self.boton_camara = ttk.Button(btn_frame, text="📷 Activar Cámara", 
                                     command=self.toggle_camara, bootstyle=INFO)
        self.boton_camara.pack(side=LEFT, padx=5)

    def crear_treeview_inventario(self, parent):
        """Crea el Treeview para mostrar el inventario"""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=True)
        
        cols = ("Producto", "Cantidad")
        self.treeview_inventario = ttk.Treeview(
            tree_frame, 
            columns=cols, 
            show=HEADINGS, 
            bootstyle=PRIMARY,
            height=15
        )
        
        for col in cols:
            self.treeview_inventario.heading(col, text=col)
            self.treeview_inventario.column(col, width=150, anchor='center')
        
        self.treeview_inventario.pack(side=LEFT, fill=BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=VERTICAL, 
                                command=self.treeview_inventario.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.treeview_inventario.configure(yscrollcommand=scrollbar.set)
        self.treeview_inventario.bind('<<TreeviewSelect>>', self.on_producto_seleccionado)
        
        # Actualizar lista con datos cargados
        self.actualizar_lista()

    def crear_botones_accion(self, parent):
        """Crea los botones de acciones para el inventario"""
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=X, pady=5)
        
        ttk.Button(action_frame, text="🍴 Consumir", 
                  command=self.consumir_producto_seleccionado, 
                  bootstyle=DANGER).pack(side=LEFT, padx=5)
        ttk.Button(action_frame, text="🗑️ Eliminar", 
                  command=self.eliminar_producto_seleccionado, 
                  bootstyle=(OUTLINE, DANGER)).pack(side=LEFT, padx=5)
        self.boton_exportar = ttk.Button(action_frame, text="📤 Exportar", 
                                       command=self.mostrar_menu_exportacion, 
                                       bootstyle=WARNING)
        self.boton_exportar.pack(side=LEFT, padx=5)
        
        # Botón para guardar inventario
        ttk.Button(action_frame, text="💾 Guardar", 
                  command=self.guardar_inventario, 
                  bootstyle=SUCCESS).pack(side=RIGHT, padx=5)

    def crear_vista_camara(self, parent):
        """Crea el panel para la vista previa de la cámara"""
        camera_card = ttk.Labelframe(parent, text="📷 Cámara", bootstyle=INFO)
        camera_card.pack(fill=BOTH, expand=True)
        
        self.placeholder_img = self.crear_placeholder()
        self.label_preview = ttk.Label(camera_card, image=self.placeholder_img)
        self.label_preview.image = self.placeholder_img
        self.label_preview.pack(padx=5, pady=5)

    def configurar_geometria(self):
        """Configura los pesos de la geometría para expansión adecuada"""
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
    # Métodos de funcionalidad
    def buscar_producto(self, event=None):
        """Filtra los productos en el inventario según el texto de búsqueda"""
        busqueda = self.entry_buscar.get().lower()
        
        # Limpiar treeview
        for row in self.treeview_inventario.get_children():
            self.treeview_inventario.delete(row)
        
        # Mostrar solo coincidencias
        for producto, cantidad in self.inventario.items():
            if busqueda in producto.lower():
                self.treeview_inventario.insert("", "end", values=(producto, cantidad))

    def agregar_producto(self):
        """Agrega o actualiza un producto en el inventario"""
        nombre = self.entry_nombre.get().strip()
        cantidad = self.cantidad_var.get()
        codigo = self.entry_codigo.get().strip()

        if not nombre:
            messagebox.showwarning("Campo requerido", "El nombre del producto es obligatorio.")
            return
            
        if cantidad <= 0:
            messagebox.showwarning("Cantidad inválida", "La cantidad debe ser mayor que cero.")
            return
        
        if nombre in self.inventario:
            self.inventario[nombre] = cantidad
            mensaje = f"Cantidad de '{nombre}' actualizada a {cantidad}."
        else:
            self.inventario[nombre] = cantidad
            mensaje = f"Producto '{nombre}' agregado con cantidad {cantidad}."
        
        messagebox.showinfo("Operación exitosa", mensaje)
        self.actualizar_lista()
        self.buscar_producto()
        self.entry_codigo.delete(0, tk.END)
        self.entry_nombre.delete(0, tk.END)
        self.cantidad_var.set(1)
        self.entry_nombre.focus_set()

    def on_producto_seleccionado(self, event):
        """Maneja la selección de productos en el Treeview"""
        seleccion = self.treeview_inventario.selection()
        if not seleccion:
            return
        
        # Tomar el último item seleccionado
        item_seleccionado = seleccion[-1]
        
        try:
            valores = self.treeview_inventario.item(item_seleccionado)['values']
            if len(valores) >= 2:
                producto, cantidad = valores[0], valores[1]
                self.entry_nombre.delete(0, tk.END)
                self.entry_nombre.insert(0, producto)
                self.cantidad_var.set(cantidad)
        except Exception as e:
            print(f"Error al obtener item seleccionado: {e}")
            messagebox.showerror("Error", "No se pudo cargar la información del producto")

    def eliminar_producto_seleccionado(self):
        """Elimina el producto seleccionado del inventario"""
        seleccion = self.treeview_inventario.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Por favor, seleccione un producto de la lista.")
            return
        
        # Tomar el último item seleccionado
        item_seleccionado = seleccion[-1]
        producto = self.treeview_inventario.item(item_seleccionado)['values'][0]
        
        confirmacion = messagebox.askyesno(
            "Confirmar eliminación", 
            f"¿Está seguro que desea eliminar '{producto}' del inventario?"
        )
        
        if confirmacion and producto in self.inventario:
            del self.inventario[producto]
            messagebox.showinfo("Producto eliminado", f"Producto '{producto}' eliminado.")
            self.actualizar_lista()
            self.buscar_producto()

    def consumir_producto_seleccionado(self):
        """Reduce la cantidad del producto seleccionado"""
        seleccion = self.treeview_inventario.selection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Por favor, seleccione un producto de la lista.")
            return
        
        # Tomar el último item seleccionado
        item_seleccionado = seleccion[-1]
        valores = self.treeview_inventario.item(item_seleccionado)['values']
        
        if len(valores) < 2:
            messagebox.showwarning("Datos incompletos", "El producto seleccionado no tiene información completa.")
            return
        
        producto = valores[0]
        cantidad = self.cantidad_var.get()
        
        if not cantidad or cantidad <= 0:
            messagebox.showwarning("Cantidad inválida", "La cantidad a consumir debe ser mayor que cero.")
            return
        
        if producto not in self.inventario:
            messagebox.showwarning("Producto no encontrado", f"El producto '{producto}' no está en el inventario.")
            return
            
        if self.inventario[producto] < cantidad:
            messagebox.showwarning(
                "Cantidad insuficiente", 
                f"No hay suficiente cantidad de '{producto}'\n"
                f"Disponible: {self.inventario[producto]}\n"
                f"Intenta consumir: {cantidad}"
            )
            return
        
        self.inventario[producto] -= cantidad
        if self.inventario[producto] <= 0:
            del self.inventario[producto]
            mensaje = f"Producto '{producto}' consumido completamente."
        else:
            mensaje = f"Producto '{producto}' consumido. Restante: {self.inventario[producto]}"
        
        messagebox.showinfo("Consumo registrado", mensaje)
        self.actualizar_lista()
        self.buscar_producto()

    def actualizar_lista(self):
        """Actualiza el Treeview con los datos actuales del inventario"""
        for row in self.treeview_inventario.get_children():
            self.treeview_inventario.delete(row)
        
        # Ordenar productos alfabéticamente
        productos_ordenados = sorted(self.inventario.items(), key=lambda x: x[0].lower())
        
        for producto, cantidad in productos_ordenados:
            self.treeview_inventario.insert("", "end", values=(producto, cantidad))

    def incrementar_cantidad(self):
        """Incrementa la cantidad en 1"""
        self.cantidad_var.set(self.cantidad_var.get() + 1)

    def decrementar_cantidad(self):
        """Decrementa la cantidad en 1 (mínimo 1)"""
        if self.cantidad_var.get() > 1:
            self.cantidad_var.set(self.cantidad_var.get() - 1)

    def exportar_a_csv(self):
        """Exporta el inventario a un archivo CSV"""
        if not self.inventario:
            messagebox.showwarning("Inventario vacío", "No hay datos para exportar.")
            return
        
        fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nombre_archivo = f"inventario_{fecha_actual}.csv"
        
        archivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
            initialfile=nombre_archivo
        )
        
        if archivo:
            try:
                with open(archivo, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Producto", "Cantidad"])
                    for producto, cantidad in sorted(self.inventario.items()):
                        writer.writerow([producto, cantidad])
                messagebox.showinfo("Exportación exitosa", f"Inventario exportado correctamente a:\n{archivo}")
            except Exception as e:
                messagebox.showerror("Error al exportar", f"No se pudo exportar el archivo:\n{str(e)}")

    def exportar_a_excel(self):
        """Exporta el inventario a un archivo Excel"""
        if not self.inventario:
            messagebox.showwarning("Inventario vacío", "No hay datos para exportar.")
            return
        
        try:
            import openpyxl
        except ImportError:
            messagebox.showerror(
                "Biblioteca no instalada", 
                "Para exportar a Excel (XLSX) necesita instalar openpyxl.\n\n"
                "Puede instalarlo con: pip install openpyxl\n\n"
                "Por ahora se exportará como CSV."
            )
            self.exportar_a_csv()
            return
        
        fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nombre_archivo = f"inventario_{fecha_actual}.xlsx"
        
        archivo = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")],
            initialfile=nombre_archivo
        )
        
        if archivo:
            try:
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Inventario"
                
                ws.append(["Producto", "Cantidad"])
                
                for producto, cantidad in sorted(self.inventario.items()):
                    ws.append([producto, cantidad])
                
                ws.column_dimensions['A'].width = 50
                ws.column_dimensions['B'].width = 15
                
                wb.save(archivo)
                messagebox.showinfo("Exportación exitosa", f"Inventario exportado correctamente a:\n{archivo}")
            except Exception as e:
                messagebox.showerror("Error al exportar", f"No se pudo exportar el archivo:\n{str(e)}")

    def mostrar_menu_exportacion(self):
        """Muestra un menú emergente con opciones de exportación"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Exportar a CSV", command=self.exportar_a_csv)
        menu.add_command(label="Exportar a Excel (XLSX)", command=self.exportar_a_excel)
        
        try:
            menu.tk_popup(
                self.boton_exportar.winfo_rootx(),
                self.boton_exportar.winfo_rooty() + self.boton_exportar.winfo_height()
            )
        finally:
            menu.grab_release()

    def toggle_camara(self):
        """Activa o desactiva la cámara para escanear códigos de barras"""
        if not self.preview_active:
            # Intentar iniciar la cámara
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Error", "No se pudo acceder a la cámara")
                self.cap = None
                return
            
            self.preview_active = True
            self.boton_camara.config(text="Detener Cámara", bootstyle=DANGER)
            self.mostrar_preview()
        else:
            # Detener la cámara
            self.preview_active = False
            if self.cap:
                self.cap.release()
                self.cap = None
            self.label_preview.config(image=self.placeholder_img)
            self.boton_camara.config(text="📷 Activar Cámara", bootstyle=INFO)

    def mostrar_preview(self):
        """Muestra la vista previa de la cámara y detecta códigos de barras"""
        if self.preview_active and self.cap:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                frame = cv2.resize(frame, (320, 240))
                
                # Detección de códigos de barras
                self.procesar_codigos_barras(frame)
                
                # Mostrar frame en la interfaz
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.label_preview.imgtk = imgtk
                self.label_preview.config(image=imgtk)
            
            # Programar próxima actualización
            self.label_preview.after(10, self.mostrar_preview)

    def procesar_codigos_barras(self, frame):
        """Procesa los códigos de barras detectados en el frame"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            barcodes = pyzbar.decode(gray)
            
            for barcode in barcodes:
                barcode_data = barcode.data.decode("utf-8")
                barcode_type = barcode.type
                
                # Dibujar rectángulo alrededor del código
                (x, y, w, h) = barcode.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Actualizar interfaz con el código detectado
                self.entry_codigo.delete(0, tk.END)
                self.entry_codigo.insert(0, barcode_data)
                
                # Obtener nombre del producto si es posible
                nombre_producto = self.obtener_producto_open_food_facts(barcode_data)
                self.entry_nombre.delete(0, tk.END)
                if nombre_producto != "Producto no encontrado":
                    self.entry_nombre.insert(0, nombre_producto)
                    self.cantidad_var.set(1)  # Resetear cantidad
                    self.entry_nombre.focus_set()  # Poner foco en nombre para edición
        except Exception as e:
            print(f"Error al procesar código de barras: {e}")

    def obtener_producto_open_food_facts(self, codigo_barras):
        """Consulta la API de Open Food Facts para obtener información del producto"""
        try:
            url = f"https://world.openfoodfacts.org/api/v0/product/{codigo_barras}.json"
            respuesta = requests.get(url, timeout=5)
            
            if respuesta.status_code == 200:
                datos = respuesta.json()
                if datos.get('product'):
                    producto = datos['product']
                    nombre = producto.get('product_name', 'Nombre no disponible')
                    return nombre if nombre else "Nombre no disponible"
                return "Producto no encontrado"
            return f"Error en la API (Código: {respuesta.status_code})"
        except requests.RequestException:
            return "Error de conexión"
        except Exception as e:
            print(f"Error al consultar API: {e}")
            return "Error al consultar"

    def crear_placeholder(self):
        """Crea una imagen de placeholder para la vista de cámara"""
        try:
            img = Image.new('RGB', (320, 240), color='#e7e7e7')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                font = ImageFont.load_default()
                
            text = "Vista previa de cámara"
            w, h = draw.textsize(text, font=font)
            draw.text(((320-w)/2, (240-h)/2), text, fill="black", font=font)
            
            return ImageTk.PhotoImage(img)
        except Exception:
            img = Image.new('RGB', (320, 240), color='#e7e7e7')
            return ImageTk.PhotoImage(img)

    def cargar_inventario(self):
        """Carga el inventario desde un archivo JSON si existe"""
        if os.path.exists(self.archivo_inventario):
            try:
                with open(self.archivo_inventario, 'r', encoding='utf-8') as f:
                    self.inventario = json.load(f)
            except Exception as e:
                print(f"Error al cargar inventario: {e}")
                messagebox.showwarning(
                    "Error", 
                    "No se pudo cargar el inventario previo. Se creará uno nuevo."
                )

    def guardar_inventario(self):
        """Guarda el inventario actual en un archivo JSON"""
        try:
            with open(self.archivo_inventario, 'w', encoding='utf-8') as f:
                json.dump(self.inventario, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Guardado", "Inventario guardado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el inventario:\n{str(e)}")

    def cerrar_aplicacion(self):
        """Maneja el cierre seguro de la aplicación"""
        if self.preview_active and self.cap:
            self.cap.release()
        
        # Preguntar si desea guardar antes de salir
        if messagebox.askyesno("Salir", "¿Desea guardar el inventario antes de salir?"):
            self.guardar_inventario()
        
        self.root.destroy()

    def __del__(self):
        """Destructor para liberar recursos de la cámara"""
        if hasattr(self, 'cap') and self.cap and self.cap.isOpened():
            self.cap.release()

if __name__ == "__main__":
    root = ttk.Window(title="Inventario de Alimentos", themename="morph")
    app = InventarioApp(root)
    root.mainloop()