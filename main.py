import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sqlite3
from datetime import datetime
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pyttsx3


class ToDoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CRM Manager")
        self.root.geometry("1200x550")

        # Create the SQLite databases
        self.todo_conn = sqlite3.connect('todo.db')
        self.operations_conn = sqlite3.connect('operations.db')
        self.todo_cursor = self.todo_conn.cursor()
        self.operations_cursor = self.operations_conn.cursor()
        self.create_todo_db()
        self.create_operations_db()

        # Create the input fields and buttons
        self.create_widgets()

        # Start the reminder
        self.remind()

    def create_todo_db(self):
        self.todo_cursor.execute('''CREATE TABLE IF NOT EXISTS todo
                            (section TEXT, name TEXT, date TEXT, time TEXT, alarm INTEGER, timestamp TEXT)''')

    def create_operations_db(self):
        self.operations_cursor.execute('''CREATE TABLE IF NOT EXISTS operations
                                (operation TEXT, timestamp TEXT, name TEXT, date TEXT, time TEXT, new_date TEXT, new_time TEXT)''')

    def add_item(self):
        name = self.name_entry.get()
        date = self.date_entry.get()
        time = self.time_entry.get()
        followup_date = self.followup_date_entry.get()  # get the new follow-up date
        followup_time = self.followup_entry.get()  # get the new follow-up time
        alarm = self.alarm_var.get()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if name and date and time and followup_date:
            if alarm:
                section = "alarm"
            else:
                section = self.section_var.get()

            self.insert_into_todo_db(section, name, date, time, alarm, timestamp)
            self.insert_into_operations_db("add_item", name, date, time)
            self.update_all_lists()
            self.update_followup_fields()  # update follow-up fields after adding an item
        else:
            messagebox.showerror("Error", "Please fill all fields")

    def remove_item(self):
        # Check if any item is selected
        any_item_selected = False

        for section in self.sections + ["alarm"]:
            treeview = self.treeviews[section]
            selected_items = treeview.selection()
            if selected_items:
                any_item_selected = True

                # Remove selected items from the specific section
                for item in selected_items:
                    item_data = treeview.item(item, "values")
                    if item_data:
                        self.delete_from_todo_db(section, item_data[0], item_data[1], item_data[2])
                        self.insert_into_operations_db("remove_item", item_data[0], item_data[1], item_data[2])
                    else:
                        messagebox.showerror("Error", "Invalid item data")

                self.update_all_lists()
                break

        if not any_item_selected:
            messagebox.showerror("Error", "No item selected")

    def move_item_up(self):
        treeviews = [self.treeviews[section] for section in self.sections]
        item_data = None

        for idx, treeview in enumerate(treeviews):
            selected_items = treeview.selection()
            if selected_items:  # if there are selected items
                item_data = treeview.item(selected_items[0], "values")
                if idx > 0:  # if it's not the first treeview
                    self.update_todo_db_section(item_data[0], item_data[1], item_data[2], self.sections[idx - 1])
                    new_date = self.followup_date_entry.get()
                    new_time = self.followup_entry.get()
                    self.update_todo_db_date(item_data[0], item_data[1], item_data[2], new_date)
                    self.update_todo_db_time(item_data[0], new_date, item_data[2], new_time)
                    self.insert_into_operations_db("move_item_up", item_data[0], item_data[1], item_data[2], new_date, new_time)
                break  # we found our selected item, no need to continue the loop

        if item_data is not None:
            self.update_all_lists()

    def move_item_down(self):
        treeviews = [self.treeviews[section] for section in self.sections]
        item_data = None

        for idx, treeview in enumerate(treeviews):
            selected_items = treeview.selection()
            if selected_items:  # if there are selected items
                item_data = treeview.item(selected_items[0], "values")
                if idx < len(treeviews) - 1:  # if it's not the last treeview
                    self.update_todo_db_section(item_data[0], item_data[1], item_data[2], self.sections[idx + 1])
                    new_date = self.followup_date_entry.get()
                    new_time = self.followup_entry.get()
                    self.update_todo_db_date(item_data[0], item_data[1], item_data[2], new_date)
                    self.update_todo_db_time(item_data[0], new_date, item_data[2], new_time)
                    self.insert_into_operations_db("move_item_down", item_data[0], item_data[1], item_data[2], new_date, new_time)
                break  # we found our selected item, no need to continue the loop

        if item_data is not None:
            self.update_all_lists()


    def update_followup_fields(self, event=None):
        selected_items = self.treeviews['follow-up'].selection()
        if selected_items:  # if there are selected items
            item_data = self.treeviews['follow-up'].item(selected_items[0], "values")
            self.followup_entry.delete(0, tk.END)
            self.followup_entry.insert(0, item_data[2])  # set the follow-up time
            self.followup_date_entry.delete(0, tk.END)
            self.followup_date_entry.insert(0, item_data[1])  # set the follow-up date
        else:
            self.followup_entry.delete(0, tk.END)
            self.followup_date_entry.delete(0, tk.END)

    def update_todo_db_time(self, name, date, old_time, new_time):
        self.todo_cursor.execute("UPDATE todo SET time = ? WHERE name=? AND date=? AND time=?",
                                (new_time, name, date, old_time))
        self.todo_conn.commit()

    def update_todo_db_section(self, name, date, time, new_section):
        self.todo_cursor.execute("UPDATE todo SET section = ? WHERE name=? AND date=? AND time=?",
                                (new_section, name, date, time))
        self.todo_conn.commit()

    def update_todo_db_date(self, name, old_date, time, new_date):
        self.todo_cursor.execute("UPDATE todo SET date = ? WHERE name=? AND date=? AND time=?",
                                 (new_date, name, old_date, time))
        self.todo_conn.commit()

    def delete_from_todo_db(self, section, name, date, time):
        print(f"Deleting {section}, {name}, {date}, {time} from todo database")  # add this
        self.todo_cursor.execute("DELETE FROM todo WHERE section=? AND name=? AND date=? AND time=?",
                                 (section, name, date, time))
        self.todo_conn.commit()

    def insert_into_todo_db(self, section, name, date, time, alarm, timestamp):
        self.todo_cursor.execute("INSERT INTO todo VALUES (?, ?, ?, ?, ?, ?)",
                                 (section, name, date, time, alarm, timestamp))
        self.todo_conn.commit()

    def insert_into_operations_db(self, operation, name=None, date=None, time=None, new_date=None, new_time=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.operations_cursor.execute("INSERT INTO operations (operation, timestamp, name, date, time) VALUES (?, ?, ?, ?, ?)",
                                    (operation, timestamp, name, date, time))
        self.operations_conn.commit()

    def get_all_items(self):
        self.todo_cursor.execute("SELECT section, name, date, time, alarm, timestamp FROM todo")
        return self.todo_cursor.fetchall()

    def get_all_items_from_section(self, section):
        self.todo_cursor.execute("SELECT name, date, time FROM todo WHERE section=?", (section,))
        return self.todo_cursor.fetchall()

    def update_all_lists(self):
        for section in self.sections:
            treeview = self.treeviews[section.lower()]
            self.update_treeview(treeview, section.capitalize())

        self.update_alarm_list()
        self.update_followup_fields()  # update follow-up fields after updating the lists

    def update_treeview(self, treeview, section):
        for item in treeview.get_children():
            treeview.delete(item)
        items = self.get_all_items_from_section(section.lower())
        for item in items:
            treeview.insert("", "end", values=item)

    def update_alarm_list(self):
        self.alarm_treeview.delete(*self.alarm_treeview.get_children())
        alarm_items = self.get_all_items_from_section('alarm')
        for item in alarm_items:
            self.alarm_treeview.insert("", "end", values=item)

    def remind(self):
        engine = pyttsx3.init()
        items = self.get_all_items()
        for item in items:
            section, name, date, task_time, alarm, timestamp = item
            current_date = datetime.now().strftime("%m/%d/%Y")
            current_time = datetime.now().strftime("%H:%M")

            if date == current_date and task_time == current_time and alarm:
                engine.say(f"It's time for {name}")
                engine.runAndWait()
                messagebox.showinfo("Reminder", f"It's time for {name}")
                time.sleep(3)

        self.root.after(45000, self.remind)

    def create_widgets(self):
        self.sections = ["prospective", "inquiry", "current", "follow-up"]
        self.treeviews = {}

        # Input fields in a single row
        self.input_frame = tk.Frame(self.root)
        self.input_frame.grid(row=0, column=0, columnspan=4)

        # To-Do Name
        self.name_label = tk.Label(self.input_frame, text="Name")
        self.name_label.grid(row=0, column=0)
        self.name_entry = tk.Entry(self.input_frame)
        self.name_entry.grid(row=0, column=1)

        # Date
        self.date_label = tk.Label(self.input_frame, text="Date (MM/DD/YYYY)")
        self.date_label.grid(row=0, column=2)
        self.date_entry = tk.Entry(self.input_frame)
        self.date_entry.grid(row=0, column=3)

        # Time
        self.time_label = tk.Label(self.input_frame, text="Time (HH:MM)")
        self.time_label.grid(row=0, column=4)
        self.time_entry = tk.Entry(self.input_frame)
        self.time_entry.grid(row=0, column=5)

        # Alarm checkbox
        self.alarm_var = tk.IntVar()
        self.alarm_checkbutton = tk.Checkbutton(self.input_frame, text="Alarm?", variable=self.alarm_var)
        self.alarm_checkbutton.grid(row=0, column=6)

        # Section dropdown
        self.section_label = tk.Label(self.input_frame, text="Section")
        self.section_label.grid(row=0, column=7)
        self.section_var = tk.StringVar()
        self.section_dropdown = ttk.Combobox(self.input_frame, textvariable=self.section_var, state="readonly")
        self.section_dropdown["values"] = self.sections
        self.section_dropdown.grid(row=0, column=8)

        # Buttons in a separate row
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.grid(row=1, column=0, columnspan=4)

        # Add and Remove buttons
        self.add_button = tk.Button(self.buttons_frame, text="+", command=self.add_item)
        self.add_button.grid(row=0, column=0)
        self.remove_button = tk.Button(self.buttons_frame, text="-", command=self.remove_item)
        self.remove_button.grid(row=0, column=1)

        self.up_button = tk.Button(self.buttons_frame, text="Up", command=self.move_item_up)
        self.up_button.grid(row=0, column=2)
        self.down_button = tk.Button(self.buttons_frame, text="Down", command=self.move_item_down)
        self.down_button.grid(row=0, column=3)

        # Follow-up time
        self.followup_label = tk.Label(self.buttons_frame, text="Next follow up time")
        self.followup_label.grid(row=0, column=4)
        self.followup_entry = tk.Entry(self.buttons_frame)
        self.followup_entry.grid(row=0, column=5)

        # Follow-up date
        self.followup_date_label = tk.Label(self.buttons_frame, text="Next follow up date")
        self.followup_date_label.grid(row=0, column=6)
        self.followup_date_entry = tk.Entry(self.buttons_frame)
        self.followup_date_entry.grid(row=0, column=7)

        # For each section, create a Treeview in a separate row
        for idx, section in enumerate(self.sections):
            section_label = tk.Label(self.root, text=section.capitalize(), font=("Helvetica", 14), pady=10)
            section_label.grid(row=2 + idx * 2, column=0, columnspan=4, sticky="w")

            treeview = ttk.Treeview(self.root, height=5)
            treeview.grid(row=3 + idx * 2, column=0, columnspan=4, sticky="nsew")
            treeview["columns"] = ("name", "date", "time")
            treeview.column("#0", width=0, stretch=tk.NO)
            treeview.column("name", anchor=tk.W, width=100)
            treeview.column("date", anchor=tk.W, width=100)
            treeview.column("time", anchor=tk.W, width=100)
            treeview.heading("#0", text="", anchor=tk.W)
            treeview.heading("name", text="Name", anchor=tk.W)
            treeview.heading("date", text="Date", anchor=tk.W)
            treeview.heading("time", text="Time", anchor=tk.W)
            self.treeviews[section] = treeview

        # Create the Treeview for the Alarms section
        # Create the Treeview for the Alarms section
        self.alarm_treeview = ttk.Treeview(self.root, height=5)
        self.treeviews['alarm'] = self.alarm_treeview
        self.alarm_treeview.grid(row=2, column=5, rowspan=len(self.sections) * 2, padx=10, sticky="nsew")
        self.alarm_treeview["columns"] = ("name", "date", "time")
        self.alarm_treeview.column("#0", width=0, stretch=tk.NO)
        self.alarm_treeview.column("name", anchor=tk.W, width=100)
        self.alarm_treeview.column("date", anchor=tk.W, width=100)
        self.alarm_treeview.column("time", anchor=tk.W, width=100)
        self.alarm_treeview.heading("#0", text="", anchor=tk.W)
        self.alarm_treeview.heading("name", text="Name", anchor=tk.W)
        self.alarm_treeview.heading("date", text="Date", anchor=tk.W)
        self.alarm_treeview.heading("time", text="Time", anchor=tk.W)

        # Ensure widgets expand to fill available space
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(4, weight=1)
        self.root.columnconfigure(5, weight=1)
        for i in range(2, 2 + len(self.sections) * 2):
            self.root.rowconfigure(i, weight=1)

        self.update_all_lists()


root = tk.Tk()
app = ToDoApp(root)
root.mainloop()
