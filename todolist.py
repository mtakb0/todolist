import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

USERS_FILE = Path("users.json")

# =======================
# THEMES
# =======================
DARK = {
    "bg": "#1e1e1e",
    "fg": "#ffffff",
    "frame": "#252526",
    "btn": "#2d2d2d",
    "btn_active": "#3c3c3c",
    "entry": "#3c3c3c",
}

LIGHT = {
    "bg": "#f5f5f5",
    "fg": "#000000",
    "frame": "#ffffff",
    "btn": "#e0e0e0",
    "btn_active": "#d0d0d0",
    "entry": "#ffffff",
}

DATE_FORMAT = "%d.%m.%Y %H:%M"
DATE_REGEX = r"^\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}$"

# =======================
# DATA MODEL
# =======================
@dataclass
class Task:
    title: str
    status: str = "todo"
    due_time: str = ""
    start_time: str = ""
    completed_time: str = ""

# =======================
# USER MANAGER
# =======================
class UserManager:
    def __init__(self):
        self.users = {}
        self.load()

    def load(self):
        if USERS_FILE.exists():
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                self.users = json.load(f)

    def save(self):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.users, f, indent=2)

    def register(self, username, password):
        if not username or not password:
            raise ValueError("Username / password can't be empty")
        if username in self.users:
            raise ValueError("This username's already exist")

        self.users[username] = {
            "password": password,
            "tasks": []
        }
        self.save()

    def login(self, username, password):
        if username not in self.users:
            raise ValueError(f"There is no user like {username}")
        if self.users[username]["password"] != password:
            raise ValueError("Wrong password")
        return self.users[username]["tasks"]

# =======================
# TODO LOGIC
# =======================
class ToDoList:
    def __init__(self, tasks, save_callback):
        self.tasks = [Task(**t) for t in tasks]
        self.save_callback = save_callback

    def validate_date(self, date_str):
        if not re.match(DATE_REGEX, date_str):
            raise ValueError("True format : 25.01.2026 18:30")
        datetime.strptime(date_str, DATE_FORMAT)

    def add(self, title, due_time):
        if not title.strip():
            raise ValueError("Can't be empty")
        self.validate_date(due_time)
        self.tasks.append(Task(title=title, due_time=due_time))
        self.save_callback(self.tasks)

    def start(self, index):
        self.tasks[index].status = "progress"
        self.tasks[index].start_time = datetime.now().strftime(DATE_FORMAT)
        self.save_callback(self.tasks)

    def finish(self, index):
        self.tasks[index].status = "done"
        self.tasks[index].completed_time = datetime.now().strftime(DATE_FORMAT)
        self.save_callback(self.tasks)

    def delete(self, index):
        self.tasks.pop(index)
        self.save_callback(self.tasks)

# =======================
# LOGIN / REGISTER
# =======================
class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.user_manager = UserManager()

        root.title("Login / Register")
        root.geometry("300x220")
        root.resizable(False, False)

        tk.Label(root, text="Username").pack(pady=(20, 0))
        self.username = tk.Entry(root)
        self.username.pack()

        tk.Label(root, text="Password").pack(pady=(10, 0))
        self.password = tk.Entry(root, show="*")
        self.password.pack()

        tk.Button(root, text="Login", command=self.login).pack(pady=8)
        tk.Button(root, text="Register", command=self.register).pack()

    def login(self):
        try:
            username = self.username.get()
            password = self.password.get()
            tasks = self.user_manager.login(username, password)

            self.root.destroy()
            main = tk.Tk()
            App(main, username, tasks, self.user_manager)
            main.mainloop()

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def register(self):
        try:
            self.user_manager.register(
                self.username.get(),
                self.password.get()
            )
            messagebox.showinfo("OK", "Register's succesfully done !")

        except ValueError as e:
            messagebox.showerror("Error", str(e))

# =======================
# MAIN APP
# =======================
class App:
    def __init__(self, root, username, tasks, user_manager):
        self.root = root
        self.username = username
        self.user_manager = user_manager

        self.todo = ToDoList(tasks, self.save_user_tasks)

        self.is_dark = True
        self.theme = DARK

        root.title(f"📝 To Do App - {username}")
        root.geometry("1000x450")

        # TOP BAR
        self.top = tk.Frame(root)
        self.top.pack(fill="x")

        tk.Label(
            self.top,
            text=f"👤 {username}",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=10)

        self.logout_btn = tk.Button(
            self.top, text="🚪 Logout",
            command=self.logout
        )
        self.logout_btn.pack(side="right", padx=10)

        self.toggle_btn = tk.Button(
            self.top, text="🌙",
            command=self.toggle_theme,
            font=("Arial", 14),
            relief="flat"
        )
        self.toggle_btn.pack(side="right")

        # ENTRY ROW
        self.entry_row = tk.Frame(root)
        self.entry_row.pack(fill="x", padx=10, pady=10)

        self.task_entry = tk.Entry(self.entry_row, font=("Arial", 14))
        self.task_entry.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.due_entry = tk.Entry(self.entry_row, font=("Arial", 14), width=20)
        self.due_entry.pack(side="right")

        self.add_btn = tk.Button(root, text="➕ Add Task", command=self.add_task)
        self.add_btn.pack(pady=5)

        # BODY
        self.body = tk.Frame(root)
        self.body.pack(expand=True, fill="both", padx=10)

        self.todo_col = self.create_column("🕒 To Do")
        self.progress_col = self.create_column("🚧 In Progress")
        self.done_col = self.create_column("✅ Finished")

        self.apply_theme()
        self.refresh()

    def logout(self):
        if messagebox.askyesno("Logout", "Do you want to logout ?"):
            self.root.destroy()
            root = tk.Tk()
            LoginWindow(root)
            root.mainloop()

    def save_user_tasks(self, tasks):
        self.user_manager.users[self.username]["tasks"] = [
            asdict(t) for t in tasks
        ]
        self.user_manager.save()

    # ---- UI & LOGIC (AYNI) ----

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.theme = DARK if self.is_dark else LIGHT
        self.toggle_btn.config(text="🌙" if self.is_dark else "☀️")
        self.apply_theme()
        self.refresh()

    def apply_theme(self):
        t = self.theme
        self.root.configure(bg=t["bg"])
        self.top.configure(bg=t["bg"])
        self.entry_row.configure(bg=t["bg"])
        self.body.configure(bg=t["bg"])

        self.task_entry.configure(bg=t["entry"], fg=t["fg"], insertbackground=t["fg"])
        self.due_entry.configure(bg=t["entry"], fg=t["fg"], insertbackground=t["fg"])

        self.add_btn.configure(bg=t["btn"], fg=t["fg"], activebackground=t["btn_active"])
        self.toggle_btn.configure(bg=t["bg"], fg=t["fg"])

    def create_column(self, title):
        frame = tk.Frame(self.body, bd=1, relief="solid")
        frame.pack(side="left", expand=True, fill="both", padx=5)

        label = tk.Label(frame, text=title, font=("Arial", 12, "bold"))
        label.pack(pady=5)

        content = tk.Frame(frame)
        content.pack(expand=True, fill="both")

        frame.label = label
        frame.content = content
        return frame

    def clear_columns(self):
        for col in (self.todo_col, self.progress_col, self.done_col):
            for w in col.content.winfo_children():
                w.destroy()

    def refresh(self):
        self.clear_columns()
        t = self.theme
        for col in (self.todo_col, self.progress_col, self.done_col):
            col.configure(bg=t["frame"])
            col.label.configure(bg=t["frame"], fg=t["fg"])
            col.content.configure(bg=t["frame"])

        for i, task in enumerate(self.todo.tasks):
            parent = (
                self.todo_col.content if task.status == "todo"
                else self.progress_col.content if task.status == "progress"
                else self.done_col.content
            )
            row = tk.Frame(parent, bg=t["frame"])
            row.pack(fill="x", pady=2)

            if task.status == "todo":
                tk.Button(row, text="Start", width=7,
                          command=lambda i=i: self.start_task(i),
                          bg=t["btn"], fg=t["fg"]).pack(side="left")
                text = f"{task.title} | Due: {task.due_time}"
            elif task.status == "progress":
                tk.Button(row, text="Finish", width=7,
                          command=lambda i=i: self.finish_task(i),
                          bg="#0DB60D", fg=t["fg"]).pack(side="left")
                text = f"{task.title} | Started: {task.start_time}"
            else:
                tk.Button(row, text="Delete", width=7,
                          command=lambda i=i: self.delete_task(i),
                          bg="#b00000", fg="white").pack(side="right")
                text = f"{task.title} | Due:{task.due_time} | Started {task.start_time} | Done: {task.completed_time}"
            tk.Label(row, text=text, bg=t["frame"], fg=t["fg"]).pack(side="left", padx=5)

    def add_task(self):
        try:
            self.todo.add(self.task_entry.get(), self.due_entry.get())
            self.task_entry.delete(0, tk.END)
            self.due_entry.delete(0, tk.END)
            self.refresh()
        except ValueError as e:
            messagebox.showerror("Hata", str(e))

    def start_task(self, index):
        self.todo.start(index)
        self.refresh()

    def finish_task(self, index):
        self.todo.finish(index)
        self.refresh()

    def delete_task(self, index):
        if messagebox.askyesno("Confirm", "Delete this task?"):
            self.todo.delete(index)
            self.refresh()

# =======================
# RUN
# =======================
if __name__ == "__main__":
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()
