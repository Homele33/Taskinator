import customtkinter as ctk
from tkcalendar import Calendar
from TaskList import TaskList

class CalendarView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.calendar = Calendar(self.master)
        self.calendar.pack(fill="x", expand=True)

        self.calendar_tree = TaskList(self.master)
