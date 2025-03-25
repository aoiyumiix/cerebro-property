import os
import tkinter as tk
from tkinter import messagebox
import psycopg2
import qrcode
from PIL import Image, ImageTk, ImageDraw, ImageFont
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
        qr_path = f"assets/qr_codes/property_id_{property_id}.png"

        cursor.execute("""
            INSERT INTO properties (property_id, purchase_date, property_name, description, qr_code)
            VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """, (property_id, purchase_date, property_name, description, qr_path))
        
        record_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Database Error", str(e))
        return

    qr_data = f"ID: {record_id}\nProperty ID: {property_id}\nPurchase Date: {purchase_date}\nProperty Name: {property_name}\nDescription: {description}"
    qr = qrcode.make(qr_data).resize((195, 195), Image.LANCZOS)

    try:
        frame = Image.open("assets/cerebro_property_id.png").resize((400, 400))
        frame.paste(qr, (100, 138))
        draw = ImageDraw.Draw(frame)
        try:
            font = ImageFont.truetype("arialbd.ttf", 18)
        except IOError:
            font = ImageFont.load_default()
        draw.text((200, 370), f"Purchase Date: {purchase_date}", fill="black", font=font, anchor="mm")
        qr_image = ImageTk.PhotoImage(frame)
        qr_label.config(image=qr_image)
        qr_label.image = qr_image
        frame.save(qr_path)
        messagebox.showinfo("Success", f"QR Code saved to {qr_path}!")
    except FileNotFoundError:
        messagebox.showerror("Error", "Template image 'cerebro_property_id.png' not found! Please check the assets folder.")

# Pagination variables
current_page = 1
items_per_page = 10

def load_properties(search_query="", page=1):
    """Load and display properties in a scrollable list with optional search filtering and pagination."""
    global current_page
    current_page = page

    for widget in property_list_frame.winfo_children():
        widget.destroy()

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Count total items for pagination
        if search_query:
            cursor.execute("""
                SELECT COUNT(*) FROM properties 
                WHERE property_id ILIKE %s OR property_name ILIKE %s
            """, (f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute("SELECT COUNT(*) FROM properties")
        total_items = cursor.fetchone()[0]
        total_pages = (total_items + items_per_page - 1) // items_per_page

        # Fetch items for the current page
        offset = (page - 1) * items_per_page
        if search_query:
            cursor.execute("""
                SELECT property_id, property_name 
                FROM properties 
                WHERE property_id ILIKE %s OR property_name ILIKE %s
                ORDER BY property_id
                LIMIT %s OFFSET %s
            """, (f"%{search_query}%", f"%{search_query}%", items_per_page, offset))
        else:
            cursor.execute("""
                SELECT property_id, property_name 
                FROM properties 
                ORDER BY property_id
                LIMIT %s OFFSET %s
            """, (items_per_page, offset))
        rows = cursor.fetchall()
        conn.close()

        # Display items
        for row in rows:
            property_frame = tb.LabelFrame(property_list_frame, text=f"Property: {row[0]}", bootstyle="secondary")  # Black outline
            property_frame.pack(fill="x", pady=5, padx=10)

            property_label = tb.Label(property_frame, text=f"Name: {row[1]}", font=("Arial", 10), anchor="w")
            property_label.pack(side="left", fill="x", expand=True, padx=10, pady=5)

            edit_button = tb.Button(property_frame, text="Edit", bootstyle="info", command=lambda p=row[0]: edit_property(p))  # Blue button
            edit_button.pack(side="right", padx=10, pady=5)

        # Pagination controls
        pagination_frame = tk.Frame(property_list_frame)
        pagination_frame.pack(fill="x", pady=10)

        if page > 1:
            prev_button = tb.Button(pagination_frame, text="Previous", bootstyle="secondary", command=lambda: load_properties(search_query, page - 1))
            prev_button.pack(side="left", padx=5)

        tb.Label(pagination_frame, text=f"Page {page} of {total_pages}", font=("Arial", 10)).pack(side="left", padx=10)

        if page < total_pages:
            next_button = tb.Button(pagination_frame, text="Next", bootstyle="secondary", command=lambda: load_properties(search_query, page + 1))
            next_button.pack(side="left", padx=5)

    except Exception as e:
        messagebox.showerror("Database Error", str(e))

def on_search():
    """Handle search input and reload the property list."""
    search_query = search_entry.get().strip()
    load_properties(search_query, page=1)

def view_property(property_id):
    """View property details and allow updates."""
    # Implement viewing and updating logic here

def edit_property(property_id):
    """Edit and update property details."""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT property_id, purchase_date, property_name, description FROM properties WHERE property_id = %s", (property_id,))
        property_data = cursor.fetchone()
        conn.close()

        if not property_data:
            messagebox.showerror("Error", "Property not found!")
            return

        # Create a new window for editing
        edit_window = tk.Toplevel(root)
        edit_window.title("Edit Property")
        edit_window.geometry("400x400")

        tb.Label(edit_window, text="Edit Property Details", font=("Arial", 15, "bold"), bootstyle="primary").pack(pady=10)

        tb.Label(edit_window, text="Property ID:", font=("Arial", 10, "bold")).pack(pady=5)
        edit_property_id = tb.Entry(edit_window, width=30, font=("Arial", 10))
        edit_property_id.insert(0, property_data[0])
        edit_property_id.pack(pady=5)
        edit_property_id.config(state="disabled")  # Make Property ID read-only

        tb.Label(edit_window, text="Purchase Date:", font=("Arial", 10, "bold")).pack(pady=5)
        edit_purchase_date = DateEntry(edit_window, dateformat="%m-%d-%Y", width=15)
        edit_purchase_date.entry.delete(0, tk.END)
        edit_purchase_date.entry.insert(0, property_data[1])
        edit_purchase_date.pack(pady=5)

        tb.Label(edit_window, text="Property Name:", font=("Arial", 10, "bold")).pack(pady=5)
        edit_property_name = tb.Entry(edit_window, width=30, font=("Arial", 10))
        edit_property_name.insert(0, property_data[2])
        edit_property_name.pack(pady=5)

        tb.Label(edit_window, text="Description:", font=("Arial", 10, "bold")).pack(pady=5)
        edit_description = tk.Text(edit_window, width=30, height=3, font=("Arial", 10))
        edit_description.insert("1.0", property_data[3])
        edit_description.pack(pady=5)

        def save_changes():
            """Save updated property details to the database."""
            updated_purchase_date = edit_purchase_date.entry.get().strip()
            updated_property_name = edit_property_name.get().strip()
            updated_description = edit_description.get("1.0", tk.END).strip()

            if not updated_property_name:
                messagebox.showerror("Error", "Property Name is required!")
                return

            try:
                conn = connect_db()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE properties
                    SET purchase_date = %s, property_name = %s, description = %s
                    WHERE property_id = %s
                """, (updated_purchase_date, updated_property_name, updated_description, property_id))
                conn.commit()
                cursor.close()
                conn.close()
                messagebox.showinfo("Success", "Property updated successfully!")
                load_properties()  # Refresh the property list
                edit_window.destroy()
            except Exception as e:
                messagebox.showerror("Database Error", str(e))

        tb.Button(edit_window, text="Save Changes", bootstyle="success", command=save_changes).pack(pady=10)

    except Exception as e:
        messagebox.showerror("Database Error", str(e))

root = tb.Window(themename="flatly")
root.title("CEREBRO Property QR Code Generator")
root.geometry("600x800")  # Increased size for better layout

# Header with a bold title and subtle background
header_frame = tk.Frame(root, bg="#f8f9fa", height=80)
header_frame.pack(fill="x", padx=10, pady=10)

try:
    logo_image = Image.open("assets/logo.png").resize((175, 78))
    logo_photo = ImageTk.PhotoImage(logo_image)
    logo_label = tk.Label(header_frame, image=logo_photo, bg="#f8f9fa")
    logo_label.image = logo_photo
    logo_label.pack(side="left", padx=10)
except FileNotFoundError:
    logo_label = tk.Label(header_frame, text="Logo Not Found", bg="#f8f9fa", font=("Arial", 12, "bold"))
    logo_label.pack(side="left", padx=10)

header_title = tk.Label(header_frame, text="CEREBRO Property Management", font=("Arial", 20, "bold"), bg="#f8f9fa", fg="#343a40")
header_title.pack(side="left", padx=20)

# Scrollable content frame
scroll_frame = ScrolledFrame(root, autohide=True)
scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
content_frame = scroll_frame

# Title for the main section
tb.Label(content_frame, text="PROPERTY IDENTIFICATION TAG", font=("Arial", 18, "bold"), bootstyle="primary").pack(pady=10)

# Entry container with rounded corners
entry_container = tb.LabelFrame(content_frame, text="Property Details", bootstyle="info", padding=10)
entry_container.pack(padx=10, pady=10, fill="x")

tb.Label(entry_container, text="Property ID:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="e")
entry_property_id = tb.Entry(entry_container, width=30, font=("Arial", 12), justify="center")
entry_property_id.grid(row=0, column=1, padx=5, pady=5, columnspan=2)

tb.Label(entry_container, text="Purchase Date:", font=("Arial", 12, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="e")
purchase_date_entry = DateEntry(entry_container, dateformat="%m-%d-%Y", width=15)
purchase_date_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=2)

tb.Label(entry_container, text="Property Name:", font=("Arial", 12, "bold")).grid(row=2, column=0, padx=5, pady=5, sticky="e")
entry_property_name = tb.Entry(entry_container, width=30, font=("Arial", 12), justify="center")
entry_property_name.grid(row=2, column=1, padx=5, pady=5, columnspan=2)

tb.Label(entry_container, text="Description:", font=("Arial", 12, "bold")).grid(row=3, column=0, padx=5, pady=5, sticky="e")
text_description = tk.Text(entry_container, width=30, height=3, font=("Arial", 12))
text_description.grid(row=3, column=1, padx=5, pady=5, columnspan=2)

btn_generate = tb.Button(content_frame, text="Generate & Save QR Code", bootstyle="success-outline", command=generate_qr, width=30)
btn_generate.pack(pady=10)

# Add a label to inform the user about the QR code storage location
tb.Label(content_frame, text="QR Codes will be stored in: /assets/qr_codes", font=("Arial", 10, "italic"), bootstyle="secondary").pack(pady=5)

qr_label = tb.Label(content_frame, bootstyle="light")
qr_label.pack(pady=10)

# Search bar with a refresh button
search_frame = tk.Frame(content_frame)
search_frame.pack(fill="x", padx=10, pady=5)

tb.Label(search_frame, text="Search:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
search_entry = tb.Entry(search_frame, width=30, font=("Arial", 12))
search_entry.pack(side="left", padx=5)
search_button = tb.Button(search_frame, text="Search", bootstyle="primary-outline", command=on_search)
search_button.pack(side="left", padx=5)

btn_refresh = tb.Button(search_frame, text="Refresh", bootstyle="secondary-outline", command=lambda: load_properties())
btn_refresh.pack(side="left", padx=5)

# Property list frame
property_list_frame = tk.Frame(content_frame)
property_list_frame.pack(fill="both", expand=True)

load_properties()

root.mainloop()
