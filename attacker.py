import socket
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import messagebox, simpledialog

class RenameDialog:
    def __init__(self, master):
        self.master = master
        self.master.title("Rename Client")
        
        self.new_name_label = tk.Label(master, text="Enter new name:")
        self.new_name_label.pack(pady=5)
        
        self.new_name_entry = tk.Entry(master)
        self.new_name_entry.pack(pady=5)
        
        self.ok_button = tk.Button(master, text="OK", command=self.close_and_rename)
        self.ok_button.pack(pady=5)
        
    def close_and_rename(self):
        new_name = self.new_name_entry.get()
        self.master.result = new_name
        self.master.destroy()

class ClientPage:
    def __init__(self, master, client_socket, client_address, client_name, server_gui_instance):
        self.master = master
        self.master.title(f"Client: {client_address}")
        self.client_socket = client_socket
        self.client_address = client_address
        self.client_name = client_name
        self.server_gui_instance = server_gui_instance
        
        self.command_label = tk.Label(master, text="Enter command:")
        self.command_label.pack(pady=5)
        
        self.command_entry = tk.Entry(master)
        self.command_entry.pack(pady=5)
        
        self.send_button = tk.Button(master, text="Send Command", command=self.send_command)
        self.send_button.pack(pady=5)
        
        self.response_label = tk.Label(master, text="Response:")
        self.response_label.pack(pady=5)
        
        self.response_text = tk.Text(master, height=10, width=50)
        self.response_text.pack(pady=5)

        self.rename_button = tk.Button(master, text="Rename Client", command=self.open_rename_dialog)
        self.rename_button.pack(pady=5)

        self.disconnect_button = tk.Button(master, text="Disconnect Client", command=self.disconnect_client)
        self.disconnect_button.pack(pady=5)

    def send_command(self):
        command = self.command_entry.get()
        if command.strip():  
            self.client_socket.send(command.encode())
            response = self.client_socket.recv(1024).decode()
            self.response_text.insert(tk.END, response + "\n")
        else:
            messagebox.showwarning("Empty Command", "Please enter a command before sending.")
    def open_rename_dialog(self):
        dialog_window = tk.Toplevel(self.master)
        rename_dialog = RenameDialog(dialog_window)
        self.master.wait_window(dialog_window)
        new_name = dialog_window.result
        if new_name:
            self.server_gui_instance.rename_client(self.client_address, new_name)
            self.client_name = new_name
            self.master.title(f"Client: {self.client_address} - {self.client_name}")

    def disconnect_client(self):
        self.server_gui_instance.disconnect_client(self.client_address)
        self.master.destroy()

class ServerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Server GUI")
        self.master.geometry("400x350")
        
        self.label = tk.Label(master, text="Server is listening...")
        self.label.pack(pady=10)

        self.clients = {}
        self.running = True
        self.setup_server()
        
        self.clients_listbox = tk.Listbox(master, selectmode=tk.SINGLE)
        self.clients_listbox.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        self.clients_listbox.bind("<Double-Button-1>", self.open_client_page)
        
        self.command_entry = tk.Entry(master)
        self.command_entry.pack(pady=5, padx=10, fill=tk.X)

        self.send_to_all_button = tk.Button(master, text="Send to All", command=self.send_command_to_all)
        self.send_to_all_button.pack(pady=5)  

    def setup_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('127.0.0.1', 12345))
        self.server_socket.listen(5)
        threading.Thread(target=self.accept_clients).start()

    def accept_clients(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            client_ip, client_port = client_address
            self.clients[(client_ip, client_port)] = (client_socket, client_address, "Default Name")
            self.update_clients_list()
            threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()

    def handle_client(self, client_socket, client_address):
        while True:
            try:
                command = client_socket.recv(1024).decode()
                if not command:
                    break
                elif command.lower().startswith('>>download'):
                    self.handle_download_command(client_socket, command)
                elif command.lower().startswith('>>upload'):
                    self.handle_upload_command(client_socket, command)
                elif command.lower() == 'exit':
                    break
                else:
                    client_socket.send(f"Received command: {command}".encode())
            except ConnectionResetError:
                print("Connection reset by client:", client_address)
                break
        client_socket.close()
        del self.clients[client_address]
        self.update_clients_list()
        print("Connection closed with:", client_address)

    def handle_download_command(self, client_socket, command):
        parts = command.split()
        if len(parts) != 3:
            client_socket.send("Invalid download command format.".encode())
            return

        _, file_path, destination_path = parts
        try:
            with open(file_path, 'rb') as file:
                data = file.read()
                client_socket.send(data)
                client_socket.send("Download successful.".encode())
        except FileNotFoundError:
            client_socket.send("File not found.".encode())

    def handle_upload_command(self, client_socket, command):
        parts = command.split()
        if len(parts) != 3:
            client_socket.send("Invalid upload command format.".encode())
            return

        _, file_path, destination_path = parts
        try:
            data = client_socket.recv(1024)
            with open(destination_path, 'wb') as file:
                file.write(data)
            client_socket.send("Upload successful.".encode())
        except Exception as e:
            client_socket.send(f"Upload failed: {str(e)}".encode())

    def update_clients_list(self):
        self.clients_listbox.delete(0, tk.END)
        for i, ((ip, port), (_, _, name)) in enumerate(self.clients.items()):
            self.clients_listbox.insert(tk.END, f"{i+1}. {name} - {ip}:{port}")

    def open_client_page(self, event):
        try:
            client_index = self.clients_listbox.curselection()[0]
            client_info = list(self.clients.keys())[client_index]
            client_socket, client_address, client_name = self.clients[client_info]
            client_page_window = tk.Toplevel(self.master)
            client_page = ClientPage(client_page_window, client_socket, client_address, client_name, self)
        except IndexError:
            pass
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def send_command_to_all(self):
        command = self.command_entry.get()
        if command.strip():  
            for client_info, (client_socket, _, _) in self.clients.items():
                client_socket.send(command.encode())


def main():
    root = tk.Tk()
    server_gui = ServerGUI(root)
    
    def on_closing():
        for client_info, (client_socket, _, _) in server_gui.clients.items():
            client_socket.close()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
