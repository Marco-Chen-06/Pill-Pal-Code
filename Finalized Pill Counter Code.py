import tkinter as tk
from tkinter import font
import RPi.GPIO as GPIO
import time

# Materials:
# Raspberry Pi 4B
# IR Sensor (FC 51 Obstacle Sensor)
# Stepper Motor (ULN2003)

GPIO.setmode(GPIO.BOARD)
sensor_pin = 31
ControlPin = [32, 36, 38, 40]
reached_prescription = False
counted_object = False
failsafe_count = 0

GPIO.setup(sensor_pin, GPIO.IN)

for pin in ControlPin:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

# ceates an array to define a sequence of rotation for the stepper motor
seq_forward = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]
seq_reverse = [
    [1, 0, 0, 1],
    [0, 0, 0, 1],
    [0, 0, 1, 1],
    [0, 0, 1, 0],
    [0, 1, 1, 0],
    [0, 1, 0, 0],
    [1, 1, 0, 0],
    [1, 0, 0, 0]
]

# creates main window for the pill counter interface
root = tk.Tk()
root.title("Main Window")
root.geometry("1150x600")
root.configure(bg="light blue")
question_font = font.Font(size = 47)
confirm_font = font.Font(size = 30)

# centers window based on width and height of window
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    window.geometry(f"{width}x{height}+{x}+{y}")




# opens a popup asking how many pills the user wants to count
def open_pill_question_popup():
    root.withdraw()
    # creates a top level window for the pill question popup
    popup_window = tk.Toplevel(root)
    popup_window.configure(bg="light blue")
    popup_window.geometry("1350x700")
    popup_window.title("Pill Counting Popup")
    center_window(popup_window, 1350, 700)

    # creates label to ask the user how many pills they want counted
    question_label = tk.Label(popup_window, text="How many pills would you like to count?", font=question_font, pady=70)
    question_label.configure(bg = "light blue")
    question_label.pack()

    # creates entry widget for the user to input the pill amount
    input_entry = tk.Entry(popup_window, width=15,  font=question_font)
    input_entry.pack(pady = 50)  # Adds padding to the bottom of the textbox

    # creates confirmation button to submit the pill amount
    confirm_button = tk.Button(popup_window, text="Confirm", command=lambda: start_counting(input_entry, popup_window), font=confirm_font, width=21, height=3)
    confirm_button.pack(pady = 45)  # Adds padding to the bottom of the confirm button



# opens the counting window
def start_counting(entry_widget, popup_window):
    global pill_count
    user_input = entry_widget.get()

    # checks if the input is a valid integer or not (defensive coding!)
    try:
        pill_count = int(user_input)
    except ValueError:
        pill_count = 0

    popup_window.destroy()
    open_counting_window()

# creates a counting window with nested popups to allow for a pill-counter feedback loop
def open_counting_window():

    counting_window = tk.Toplevel(root)
    counting_window.title("Counting Window")
    counting_window.geometry("1350x700")
    counting_window.configure(bg="light blue")
    center_window(counting_window, 1350, 700)

    def increment_count(event):
        global current_count
        current_count += 1
        count_label.config(text=f"Current Count: {current_count}/{pill_count}")
        if current_count == pill_count:
            complete_popup()

    def complete_popup():
        complete_label.config(text="Counting Completed!")
        count_same_button.pack(pady = 30)
        count_new_button.pack(pady = 30)

    # lets user stay with the same pill counting amount
    def reset_count_same():
        global reached_prescription
        global counted_object
        global current_count
        global failsafe_count
        current_count = 0
        reached_prescription = False
        counted_object = False
        failsafe_count = 0

        count_label.config(text=f"Current Count: {current_count}/{pill_count}")
        complete_label.config(text="")
        count_same_button.pack_forget()
        count_new_button.pack_forget()
        check_object_count()

    # lets user change the pill counting amount
    def reset_count_new():
        global reached_prescription
        global counted_object
        global current_count
        global failsafe_count
        current_count = 0
        reached_prescription = False
        counted_object = False
        failsafe_count = 0

        count_label.config(text=f"Current Count: {current_count}/{pill_count}")
        complete_label.config(text="")
        count_same_button.pack_forget()
        count_new_button.pack_forget()
        counting_window.destroy()
        open_pill_question_popup()

    current_count = 0

    count_label = tk.Label(counting_window, text=f"Current Count: {current_count}/{pill_count}", font=question_font, pady=50)
    count_label.configure(bg="light blue")
    count_label.pack()

    complete_label = tk.Label(counting_window, text="", font=question_font, pady=50)
    complete_label.configure(bg="light blue")
    complete_label.pack()

    count_same_button = tk.Button(counting_window, text="Count Same", command=lambda: reset_count_same(), font=confirm_font, width=15, height=2)
    count_new_button = tk.Button(counting_window, text="Count New", command=lambda: reset_count_new(), font=confirm_font, width=15, height=2)

# function to periodically check for object counts w/ the IR sensor
    def check_object_count():
        global failsafe_count
        global reached_prescription
        global counted_object
        global current_count
        global pill_count
        if current_count >= pill_count:
            reached_prescription = True
        if not reached_prescription:
            for step in seq_forward:
                for pin in range(4):
                    GPIO.output(ControlPin[pin], step[pin])
                time.sleep(0.001)
        else:
            for step in seq_reverse:
                for pin in range(4):
                    GPIO.output(ControlPin[pin], step[pin])    
                time.sleep(0.001)

        if not GPIO.input(sensor_pin):
            if not counted_object:
                increment_count(None)
               
                print("Item count: " + str(current_count))
                counted_object = True
        else:
            counted_object = False
       
        # next check is after 2 milliseconds if prescription isn't reached
        if not reached_prescription:
            counting_window.after(2, check_object_count)
        else:
            # only checks after 2 milliseconds if failsafe_count is less than 500
            if failsafe_count < 200:
                counting_window.after(2, check_object_count)
                failsafe_count += 1

    # checks for object counts
    check_object_count()

# creates label to display the opening welcome message
question_label = tk.Label(root, text="Welcome to the Pill Counter Interface!", font=question_font, pady=125)
question_label.configure(bg="light blue")
center_window(root, 1350, 700)
question_label.pack()

# creates button to open the pill counting popup question
open_popup_button = tk.Button(root, text="Start Counting!", font = confirm_font, command=open_pill_question_popup, width=27, height=4)
open_popup_button.pack()

# initializes pill_count and current_count variables
pill_count = 0
current_count = 0

# starts the code loop
root.mainloop()









