import tkinter as tk
from tkinter import filedialog
import ocrmypdf
import os

def convert_to_pdf(input_jpeg_file, output_directory, index):
    output_pdf_file = os.path.join(output_directory, f"invoice_converted_{index}.pdf")
    ocrmypdf.ocr(input_jpeg_file, output_pdf_file)
    return output_pdf_file

def convert_images():
    input_files = filedialog.askopenfilenames(title="Select JPEG Files", filetypes=[("JPEG Files", "*.jpg *.jpeg")])
    if not input_files:
        status_label.config(text="No images selected.")
        return

    index = 1

    for input_file in input_files:
        output_directory = os.path.join(os.path.dirname(input_file), "pdf")  # Output directory is created in the same folder as the input file

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        pdf_file = convert_to_pdf(input_file, output_directory, index)
        print(f'Converted {input_file} to {pdf_file}')

        index += 1

    status_label.config(text=f"Conversion completed. {len(input_files)} images converted to PDF.")

root = tk.Tk()
root.title("JPEG to PDF Converter")


convert_button = tk.Button(root, text="Convert JPEG to PDF", command=convert_images)
convert_button.pack(pady=20)

status_label = tk.Label(root, text="")
status_label.pack()

root.mainloop()
