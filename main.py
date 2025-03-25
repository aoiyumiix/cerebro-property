import tkinter as tk
from tkinter import filedialog, messagebox
import qrcode
from PIL import Image, ImageTk, ImageDraw, ImageFont
import ttkbootstrap as tb
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.widgets import DateEntry
import win32print  # For Windows printing
import win32ui
import win32con

def generate_qr():
    global saved_qr

    property_id = entry_property_id.get().strip()
    purchase_date = purchase_date_entry.entry.get().strip()
    property_name = entry_property_name.get().strip()
    description = text_description.get("1.0", tk.END).strip()

    if not property_id or not property_name:
        messagebox.showerror("Error", "Property ID and Name are required!")
        return

    qr_data = f"Property ID: {property_id}\nPurchase Date: {purchase_date}\nProperty Name: {property_name}\nDescription: {description}"
    qr = qrcode.make(qr_data)
    qr = qr.resize((195, 195), Image.LANCZOS)

    try:
        frame = Image.open("CEREBRO PROPERTY ID.png")  
        frame = frame.resize((400, 400))
        frame.paste(qr, (100, 138))

        draw = ImageDraw.Draw(frame)

        try:
            font = ImageFont.truetype("arialbd.ttf", 18)
        except IOError:
            font = ImageFont.load_default()

        draw.text((200, 365), f"Purchase Date: {purchase_date}", fill="black", font=font, anchor="mm")

        qr_image = ImageTk.PhotoImage(frame)
        qr_label.config(image=qr_image)
        qr_label.image = qr_image

        saved_qr = frame
    except FileNotFoundError:
        messagebox.showerror("Error", "CEREBRO PROPERTY ID.png not found!")

def save_qr():
    if saved_qr is None:
        messagebox.showerror("Error", "Generate a QR Code first!")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
    if file_path:
        saved_qr.save(file_path)
        messagebox.showinfo("Success", "QR Code saved successfully!")

def print_sticker():
    if saved_qr is None:
        messagebox.showerror("Error", "Generate a QR Code first!")
        return

    printer_name = win32print.GetDefaultPrinter()
    hprinter = win32print.OpenPrinter(printer_name)
    printer_info = win32print.GetPrinter(hprinter, 2)
    pdc = win32ui.CreateDC()
    pdc.CreatePrinterDC(printer_name)
    pdc.StartDoc('Sticker Print')
    pdc.StartPage()

    pdc.DrawText("CEREBRO PROPERTY ID", (10, 10, 300, 40), win32ui.DT_CENTER)
    pdc.EndPage()
    pdc.EndDoc()
    pdc.DeleteDC()
    messagebox.showinfo("Success", "Sticker printed successfully!")

root = tb.Window(themename="flatly")
root.title("CEREBRO Property QR Code Generator")
root.geometry("500x700")

header_frame = tk.Frame(root)
header_frame.pack(fill="x", padx=10, pady=10)

try:
    logo_image = Image.open("logo.png")  
    logo_image = logo_image.resize((175, 78))  
    logo_photo = ImageTk.PhotoImage(logo_image)
    logo_label = tk.Label(header_frame, image=logo_photo)
    logo_label.image = logo_photo
    logo_label.pack(side="left", padx=10)
except FileNotFoundError:
    logo_label = tk.Label(header_frame, text="Logo Not Found")
    logo_label.pack(side="left", padx=10)

scroll_frame = ScrolledFrame(root, autohide=True)
scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
content_frame = scroll_frame

tb.Label(content_frame, text="PROPERTY IDENTIFICATION TAG", font=("Arial", 15, "bold"), bootstyle="primary").pack(pady=10)

entry_wrapper = tk.Frame(content_frame)
entry_wrapper.pack(pady=10)

entry_container = tb.LabelFrame(entry_wrapper, text="Property Details", bootstyle="info")
entry_container.pack(padx=10, pady=10)

tb.Label(entry_container, text="Property ID:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_property_id = tb.Entry(entry_container, width=30, font=("Arial", 10), justify="center")
entry_property_id.grid(row=0, column=1, padx=5, pady=5, columnspan=2)

tb.Label(entry_container, text="Purchase Date:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="e")
purchase_date_entry = DateEntry(entry_container, dateformat="%m-%d-%Y", width=15)
purchase_date_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=2)

property_name_frame = tk.Frame(content_frame)
property_name_frame.pack(fill="x", pady=5)
tb.Label(property_name_frame, text="Property Name:", font=("Arial", 10, "bold")).pack()
entry_property_name = tb.Entry(property_name_frame, width=50, font=("Arial", 10), justify="center")
entry_property_name.pack(pady=5)

description_frame = tk.Frame(content_frame)
description_frame.pack(fill="x", pady=5)
tb.Label(description_frame, text="Description:", font=("Arial", 10, "bold")).pack()
text_description = tk.Text(description_frame, width=50, height=4, font=("Arial", 10))
text_description.pack(pady=5)

btn_generate = tb.Button(content_frame, text="Generate QR Code", bootstyle="info", command=generate_qr, width=25)
btn_generate.pack(pady=10)

qr_label = tb.Label(content_frame, bootstyle="light")
qr_label.pack(pady=10)

btn_save = tb.Button(content_frame, text="Save QR Code", bootstyle="success", command=save_qr, width=25)
btn_save.pack(pady=10)

btn_print = tb.Button(content_frame, text="Print Sticker", bootstyle="danger", command=print_sticker, width=25)
btn_print.pack(pady=10)

saved_qr = None

root.mainloop()
