import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import requests
import cv2
from pyzbar import pyzbar
from PIL import Image, ImageTk, ImageDraw, ImageFont
import csv
from datetime import datetime

class InventarioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventario de Alimentos")
        self.root.state('zoomed')
        self.root.config(bg="#f4f4f9")
        
        self.inventario = {}
        self.cantidad_var = tk.IntVar(value=1)
        self.cap = None
        self.preview_active = False
        
        self.configurar_estilos()
        self.crear_interfaz()
        
    def configurar_estilos(self):
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Helvetica', 12, 'bold'), padding=8)
        self.style.map('TButton', background=[('active', '#45a049'), ('pressed', '#388E3C')])
        self.style.configure('Agregar.TButton', background='#4CAF50', foreground='#4CAF50')
        self.style.configure('EliminarSel.TButton', background='#FF5733', foreground='#FF5733')
        self.style.configure('ConsumirSel.TButton', background='#9C27B0', foreground='#9C27B0')
        self.style.configure('Camara.TButton', background='#2196F3', foreground='#2196F3')
        self.style.configure('Exportar.TButton', background='#FF9800', foreground='#FF9800')
        self.style.configure('Cantidad.TButton', background='#607D8B', foreground='#607D8B')
        self.style.configure('TLabel', font=('Helvetica', 12), background='#f4f4f9', foreground='#333333')
        self.style.configure('TEntry', font=('Helvetica', 12), padding=8, relief="flat", background="#e7e7e7", foreground="#333")
        self.style.configure('Treeview', font=('Helvetica', 11), rowheight=25)
        self.style.map('Treeview', background=[('selected', '#B8D8B8')])

    def crear_interfaz(self):
        # Título
        titulo = ttk.Label(self.root, text="Inventario de Alimentos", style='TLabel', font=('Helvetica', 16, 'bold'))
        titulo.grid(row=0, column=0, columnspan=3, pady=20)

        # Frame principal
        frame_principal = ttk.Frame(self.root)
        frame_principal.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Panel izquierdo (controles)
        frame_controles = ttk.Frame(frame_principal)
        frame_controles.grid(row=0, column=0, sticky="nsew", padx=10)
        frame_principal.grid_rowconfigure(0, weight=1)
        frame_principal.grid_columnconfigure(0, weight=1)

        # Panel derecho (cámara)
        frame_preview = ttk.Frame(frame_principal)
        frame_preview.grid(row=0, column=1, sticky="ne", padx=10)
        frame_principal.grid_columnconfigure(1, weight=0)

        # Búsqueda
        frame_busqueda = ttk.Frame(frame_controles)
        frame_busqueda.grid(row=0, column=0, pady=(0, 10), sticky="ew")

        ttk.Label(frame_busqueda, text="Buscar producto:", style='TLabel').grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_buscar = ttk.Entry(frame_busqueda, style='TEntry', width=30)
        self.entry_buscar.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entry_buscar.bind('<KeyRelease>', self.buscar_producto)

        # Registro de productos
        frame_registro = ttk.LabelFrame(frame_controles, text="Registrar/Actualizar Producto", padding=10)
        frame_registro.grid(row=1, column=0, pady=10, sticky="ew")

        # Código de barras (opcional)
        ttk.Label(frame_registro, text="Código de barras:", style='TLabel').grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_codigo = ttk.Entry(frame_registro, style='TEntry', width=30)
        self.entry_codigo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Nombre del producto (requerido)
        ttk.Label(frame_registro, text="Nombre del producto*:", style='TLabel').grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_nombre = ttk.Entry(frame_registro, style='TEntry', width=30)
        self.entry_nombre.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Cantidad con controles +/-
        ttk.Label(frame_registro, text="Cantidad*:", style='TLabel').grid(row=2, column=0, padx=5, pady=5, sticky="w")
        frame_cantidad = ttk.Frame(frame_registro)
        frame_cantidad.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ttk.Button(frame_cantidad, text="-", command=self.decrementar_cantidad, style='Cantidad.TButton', width=3).grid(row=0, column=0, padx=2)
        ttk.Entry(frame_cantidad, textvariable=self.cantidad_var, style='TEntry', width=5, justify='center').grid(row=0, column=1, padx=2)
        ttk.Button(frame_cantidad, text="+", command=self.incrementar_cantidad, style='Cantidad.TButton', width=3).grid(row=0, column=2, padx=2)

        # Botones de acción
        frame_botones_accion = ttk.Frame(frame_registro)
        frame_botones_accion.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(frame_botones_accion, text="Agregar/Actualizar", command=self.agregar_producto, style='Agregar.TButton').grid(row=0, column=0, padx=5, pady=5)
        self.boton_camara = ttk.Button(frame_botones_accion, text="Activar Cámara", command=self.toggle_camara, style='Camara.TButton')
        self.boton_camara.grid(row=0, column=1, padx=5, pady=5)

        # Lista de inventario
        frame_lista = ttk.LabelFrame(frame_controles, text="Inventario", padding=10)
        frame_lista.grid(row=2, column=0, pady=10, sticky="nsew")
        frame_controles.grid_rowconfigure(2, weight=1)
        frame_controles.grid_columnconfigure(0, weight=1)

        self.treeview_inventario = ttk.Treeview(frame_lista, columns=("Producto", "Cantidad"), show="headings", height=15)
        self.treeview_inventario.heading("Producto", text="Producto")
        self.treeview_inventario.heading("Cantidad", text="Cantidad")
        self.treeview_inventario.column("Producto", width=300)
        self.treeview_inventario.column("Cantidad", width=100)
        self.treeview_inventario.grid(row=0, column=0, sticky="nsew")
        frame_lista.grid_rowconfigure(0, weight=1)
        frame_lista.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=self.treeview_inventario.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.treeview_inventario.configure(yscrollcommand=scrollbar.set)
        self.treeview_inventario.bind('<<TreeviewSelect>>', self.on_producto_seleccionado)

        # Botones de acciones
        frame_acciones = ttk.Frame(frame_controles)
        frame_acciones.grid(row=3, column=0, pady=10, sticky="ew")

        ttk.Button(frame_acciones, text="Consumir Seleccionado", command=self.consumir_producto_seleccionado, style='ConsumirSel.TButton').grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(frame_acciones, text="Eliminar Seleccionado", command=self.eliminar_producto_seleccionado, style='EliminarSel.TButton').grid(row=0, column=1, padx=5, pady=5)
        self.boton_exportar = ttk.Button(frame_acciones, text="Exportar Inventario", command=self.mostrar_menu_exportacion, style='Exportar.TButton')
        self.boton_exportar.grid(row=0, column=2, padx=5, pady=5)

        # Vista previa de cámara
        self.placeholder_img = self.crear_placeholder()
        self.label_preview = ttk.Label(frame_preview, borderwidth=2, relief="solid", image=self.placeholder_img)
        self.label_preview.image = self.placeholder_img
        self.label_preview.grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(frame_preview, text="Vista previa de la cámara", style='TLabel').grid(row=1, column=0)

    # Resto de los métodos (agregar_producto, eliminar_producto_seleccionado, etc.) permanecen iguales
    # Solo cambia que ahora son métodos de la clase y usan self. para acceder a los atributos

    def agregar_producto(self):
        nombre = self.entry_nombre.get()
        cantidad = self.cantidad_var.get()

        if nombre and cantidad:
            if nombre in self.inventario:
                self.inventario[nombre] = int(cantidad)
                messagebox.showinfo("Cantidad actualizada", f"Cantidad de '{nombre}' actualizada a {cantidad}.")
            else:
                codigo = self.entry_codigo.get()
                self.inventario[nombre] = int(cantidad)
                messagebox.showinfo("Producto agregado", f"Producto '{nombre}' agregado con cantidad {cantidad}.")
            
            self.actualizar_lista()
            self.buscar_producto()
            self.entry_codigo.delete(0, tk.END)
        else:
            messagebox.showwarning("Campos vacíos", "Por favor, ingrese al menos el nombre del producto y cantidad.")

    def eliminar_producto_seleccionado(self):
        seleccion = self.treeview_inventario.selection()
        if seleccion:
            producto = self.treeview_inventario.item(seleccion)['values'][0]
            if producto in self.inventario:
                del self.inventario[producto]
                messagebox.showinfo("Producto eliminado", f"Producto '{producto}' eliminado.")
                self.actualizar_lista()
                self.buscar_producto()
        else:
            messagebox.showwarning("Selección requerida", "Por favor, seleccione un producto de la lista.")

    def consumir_producto_seleccionado(self):
        seleccion = self.treeview_inventario.selection()
        if seleccion:
            producto = self.treeview_inventario.item(seleccion)['values'][0]
            cantidad = self.cantidad_var.get()
            
            if cantidad:
                if producto in self.inventario:
                    cantidad_consumir = int(cantidad)
                    if self.inventario[producto] >= cantidad_consumir:
                        self.inventario[producto] -= cantidad_consumir
                        messagebox.showinfo("Producto consumido", f"Producto '{producto}' consumido. Cantidad restante: {self.inventario[producto]}.")
                        self.actualizar_lista()
                        self.buscar_producto()
                    else:
                        messagebox.showwarning("Cantidad insuficiente", f"No hay suficiente cantidad de '{producto}' en el inventario.")
                else:
                    messagebox.showwarning("Producto no encontrado", f"El producto '{producto}' no se encuentra en el inventario.")
            else:
                messagebox.showwarning("Cantidad requerida", "Por favor, ingrese la cantidad a consumir.")
        else:
            messagebox.showwarning("Selección requerida", "Por favor, seleccione un producto de la lista.")

    def actualizar_lista(self):
        for row in self.treeview_inventario.get_children():
            self.treeview_inventario.delete(row)
        for producto, cantidad in self.inventario.items():
            self.treeview_inventario.insert("", "end", values=(producto, cantidad))

    def on_producto_seleccionado(self, event):
        seleccion = self.treeview_inventario.selection()
        if seleccion:
            producto = self.treeview_inventario.item(seleccion)['values'][0]
            cantidad = self.treeview_inventario.item(seleccion)['values'][1]
            
            self.entry_nombre.delete(0, tk.END)
            self.entry_nombre.insert(0, producto)
            self.cantidad_var.set(cantidad)

    def buscar_producto(self, event=None):
        busqueda = self.entry_buscar.get().lower()
        
        for row in self.treeview_inventario.get_children():
            self.treeview_inventario.delete(row)
        
        for producto, cantidad in self.inventario.items():
            if busqueda in producto.lower():
                self.treeview_inventario.insert("", "end", values=(producto, cantidad))

    def incrementar_cantidad(self):
        self.cantidad_var.set(self.cantidad_var.get() + 1)

    def decrementar_cantidad(self):
        if self.cantidad_var.get() > 1:
            self.cantidad_var.set(self.cantidad_var.get() - 1)

    def exportar_a_csv(self):
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
                    for producto, cantidad in self.inventario.items():
                        writer.writerow([producto, cantidad])
                messagebox.showinfo("Exportación exitosa", f"Inventario exportado correctamente a:\n{archivo}")
            except Exception as e:
                messagebox.showerror("Error al exportar", f"No se pudo exportar el archivo:\n{str(e)}")

    def exportar_a_excel(self):
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
                
                for producto, cantidad in self.inventario.items():
                    ws.append([producto, cantidad])
                
                ws.column_dimensions['A'].width = 50
                ws.column_dimensions['B'].width = 15
                
                wb.save(archivo)
                messagebox.showinfo("Exportación exitosa", f"Inventario exportado correctamente a:\n{archivo}")
            except Exception as e:
                messagebox.showerror("Error al exportar", f"No se pudo exportar el archivo:\n{str(e)}")

    def mostrar_menu_exportacion(self):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Exportar a CSV", command=self.exportar_a_csv)
        menu.add_command(label="Exportar a Excel (XLSX)", command=self.exportar_a_excel)
        
        try:
            menu.tk_popup(self.boton_exportar.winfo_rootx(), self.boton_exportar.winfo_rooty() + self.boton_exportar.winfo_height())
        finally:
            menu.grab_release()

    def toggle_camara(self):
        if not self.preview_active:
            # Iniciar la cámara
            self.cap = cv2.VideoCapture(0)
            self.preview_active = True
            self.boton_camara.config(text="Detener Cámara")
            self.mostrar_preview()
        else:
            # Detener la cámara
            self.preview_active = False
            self.cap.release()
            self.label_preview.config(image=self.placeholder_img)
            self.boton_camara.config(text="Activar Cámara")

    def mostrar_preview(self):
        if self.preview_active:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                frame = cv2.resize(frame, (320, 240))
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                try:
                    barcodes = pyzbar.decode(gray)
                    for barcode in barcodes:
                        barcode_data = barcode.data.decode("utf-8")
                        barcode_type = barcode.type
                        
                        self.entry_codigo.delete(0, tk.END)
                        self.entry_codigo.insert(0, barcode_data)
                        
                        nombre_producto = self.obtener_producto_open_food_facts(barcode_data)
                        self.entry_nombre.delete(0, tk.END)
                        if nombre_producto != "Producto no encontrado":
                            self.entry_nombre.insert(0, nombre_producto)
                        else:
                            self.entry_nombre.focus_set()
                except Exception as e:
                    print(f"Error de decodificación: {e}")
                
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.label_preview.imgtk = imgtk
                self.label_preview.config(image=imgtk)
            
            self.label_preview.after(10, self.mostrar_preview)

    def obtener_producto_open_food_facts(self, codigo_barras):
        url = f"https://world.openfoodfacts.org/api/v0/product/{codigo_barras}.json"
        respuesta = requests.get(url)
        
        if respuesta.status_code == 200:
            datos = respuesta.json()
            
            if datos.get('product'):
                producto = datos['product']
                nombre = producto.get('product_name', 'Nombre no disponible')
                return nombre
            else:
                return "Producto no encontrado"
        else:
            return f"Error al consultar el producto. Código de estado: {respuesta.status_code}"

    def crear_placeholder(self):
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
        except:
            img = Image.new('RGB', (320, 240), color='#e7e7e7')
            return ImageTk.PhotoImage(img)

    def __del__(self):
        if hasattr(self, 'cap') and self.cap and self.cap.isOpened():
            self.cap.release()

if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioApp(root)
    root.mainloop()