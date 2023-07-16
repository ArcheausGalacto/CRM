import tkinter as tk
from tkinter import ttk
import sqlite3


def display_operations():
    conn_operations = sqlite3.connect('operations.db')
    cursor_operations = conn_operations.cursor()

    # Retrieve all rows from the operations table
    cursor_operations.execute("SELECT operation, timestamp, name, date, time FROM operations")
    rows_operations = cursor_operations.fetchall()

    # Create a tkinter window
    root = tk.Tk()
    root.title("Operations Log")

    # Create a Treeview widget
    treeview = ttk.Treeview(root)
    treeview["columns"] = ("operation", "timestamp", "name", "date", "time")
    treeview.column("#0", width=0, stretch=tk.NO)
    treeview.column("operation", anchor=tk.W, width=100)
    treeview.column("timestamp", anchor=tk.W, width=200)
    treeview.column("name", anchor=tk.W, width=100)
    treeview.column("date", anchor=tk.W, width=100)
    treeview.column("time", anchor=tk.W, width=100)
    treeview.heading("#0", text="", anchor=tk.W)
    treeview.heading("operation", text="Operation", anchor=tk.W)
    treeview.heading("timestamp", text="Timestamp", anchor=tk.W)
    treeview.heading("name", text="Name", anchor=tk.W)
    treeview.heading("date", text="Date", anchor=tk.W)
    treeview.heading("time", text="Time", anchor=tk.W)
    treeview.pack(fill="both", expand=True)

    # Insert data into the Treeview
    for row_operations in rows_operations:
        try:
            operation, timestamp, name, date, time = row_operations
        except ValueError:
            # Handle missing values here
            operation, timestamp, name, date = row_operations
            time = "N/A"
        treeview.insert("", "end", values=(operation, timestamp, name, date, time))

    conn_operations.close()

    root.mainloop()


display_operations()
