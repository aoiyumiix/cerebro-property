import os
import tkinter as tk
from tkinter import messagebox
import qrcode
from PIL import Image, ImageTk, ImageDraw, ImageFont
import psycopg2  # ✅ PostgreSQL library
import ttkbootstrap as tb
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.widgets import DateEntry

# Ensure 'assets/qr_codes' directory exists
os.makedirs("assets/qr_codes", exist_ok=True)

def connect_db():
    """Connect to PostgreSQL database."""
    return psycopg2.connect(
        dbname="cerebro_properties",
        user="postgres",
        password="cerebro", 
        host="localhost",
        port="5432"
    )

def generate_qr():
    """Generate and save QR Code after inserting property details into the database."""
    property_id = entry_property_id.get().strip()
    purchase_date = purchase_date_entry.entry.get().strip()
    property_name = entry_property_name.get().strip()
    description = text_description.get("1.0", tk.END).strip()

    if not property_id or not property_name:
        messagebox.showerror("Error", "Property ID and Name are required!")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # 🔹 Generate a temporary QR Code path BEFORE inserting into database
        qr_path = f"assets/qr_codes/qr_{property_id}.png"

        # 🔹 Insert data into PostgreSQL (including qr_code path)
        cursor.execute("""
            INSERT INTO properties (property_id, purchase_date, property_name, description, qr_code)
            VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """, (property_id, purchase_date, property_name, description, qr_path))
        
        record_id = cursor.fetchone()[0]  # Get inserted ID
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        messagebox.showerror("Database Error", str(e))
        return

    # 🔹 Generate QR Code (after inserting into DB)
    qr_data = f"ID: {record_id}\nProperty ID: {property_id}\nPurchase Date: {purchase_date}\nProperty Name: {property_name}\nDescription: {description}"
    qr = qrcode.make(qr_data)
    qr = qr.resize((195, 195), Image.LANCZOS)

    try:
        frame = Image.open("assets/cerebro_property_id.png")
        frame = frame.resize((400, 400))
        frame.paste(qr, (100, 138))

        # Draw purchase date text
        draw = ImageDraw.Draw(frame)
        try:
            font = ImageFont.truetype("arialbd.ttf", 20)
        except IOError:
            font = ImageFont.load_default()
            draw.text((200, 370), f"Purchase Date: {purchase_date}", fill="black", anchor="mm")
        else:
            draw.text((200, 370), f"Purchase Date: {purchase_date}", fill="black", font=font, anchor="mm")

        qr_image = ImageTk.PhotoImage(frame)
        qr_label.config(image=qr_image)
        qr_label.image = qr_image

        # ✅ Save the QR Code to the correct file path
        frame.save(qr_path)

        messagebox.showinfo("Success", f"QR Code saved to {qr_path}!")

    except FileNotFoundError:
        messagebox.showerror("Error", "Template image 'cerebro_property_id.png' not found! Please check the assets folder.")


# 🔹 Create UI Window
root = tb.Window(themename="flatly")
root.title("CEREBRO Property QR Code Generator")
root.geometry("500x700")

# Scrollable Frame
scroll_frame = ScrolledFrame(root, autohide=True)
scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
content_frame = scroll_frame

# Title Label
tb.Label(content_frame, text="CEREBRO PROPERTY ID", font=("Arial", 18, "bold"), bootstyle="primary").pack(pady=10)

# Entry Fields Container
entry_container = tb.LabelFrame(content_frame, text="Property Details", bootstyle="info")
entry_container.pack(pady=10, fill="x", padx=10)

# Property ID
tb.Label(entry_container, text="Property ID:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_property_id = tb.Entry(entry_container, width=30, font=("Arial", 10))
entry_property_id.grid(row=0, column=1, padx=5, pady=5)

# Purchase Date
tb.Label(entry_container, text="Purchase Date:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="e")
purchase_date_entry = DateEntry(entry_container, dateformat="%m-%d-%Y", width=15)
purchase_date_entry.grid(row=1, column=1, padx=5, pady=5)

# Property Name
tb.Label(content_frame, text="Property Name:", font=("Arial", 10, "bold")).pack(pady=5)
entry_property_name = tb.Entry(content_frame, width=50, font=("Arial", 10))
entry_property_name.pack(pady=5)

# Description
tb.Label(content_frame, text="Description:", font=("Arial", 10, "bold")).pack(pady=5)
text_description = tk.Text(content_frame, width=50, height=4, font=("Arial", 10))
text_description.pack(pady=5)

# Generate QR Code Button
btn_generate = tb.Button(content_frame, text="Generate & Save QR Code", bootstyle="primary", command=generate_qr, width=30)
btn_generate.pack(pady=10)

# QR Code Display
qr_label = tb.Label(content_frame, bootstyle="light")
qr_label.pack(pady=10)

# Run Application
root.mainloop()
