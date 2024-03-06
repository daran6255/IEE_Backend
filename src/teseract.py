from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QComboBox, QTextEdit, QCheckBox
import sys
import fitz  
import pytesseract
import os
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from PIL import Image

class PDFExtractorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.pdf_files = []
    
    def init_ui(self):
        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle('PDF Text Extractor')
        self.layout = QVBoxLayout()
        self.combo_box = QComboBox()
        self.combo_box.addItem("PyMuPDF + PyTesseract")
        self.browse_button = QPushButton("Browse PDF Files")
        self.browse_button.clicked.connect(self.browse_pdf_files)
        self.extract_button = QPushButton("Extract Text")
        self.extract_button.clicked.connect(self.extract_text)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.remove_newlines_checkbox = QCheckBox("Remove New Lines")
        self.layout.addWidget(self.combo_box)
        self.layout.addWidget(self.browse_button)
        self.layout.addWidget(self.extract_button)
        self.layout.addWidget(self.remove_newlines_checkbox)
        self.layout.addWidget(self.text_edit)
        self.setLayout(self.layout)

    def browse_pdf_files(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        options |= QFileDialog.DontUseNativeDialog 
        pdf_files, _ = QFileDialog.getOpenFileNames(self, "Select PDF Files", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if pdf_files:
            self.pdf_files = pdf_files

    def extract_text(self):
        if not self.pdf_files:
            self.text_edit.setPlainText("No PDF files selected.")
            return
        selected_method = self.combo_box.currentText()
        for index, pdf_file in enumerate(self.pdf_files, 1):
            extracted_text = ""
            try:
                # if pdf_file is pdf:
                doc = fitz.open(pdf_file)
                for page in doc:
                    extracted_text += page.get_text()
                doc.close()
                if selected_method == "PyMuPDF + PyTesseract":

                    extracted_text = pytesseract.image_to_string(extracted_text)
                # elif pdf_file is jpg/jpeg:
                    # custom_config = r'--oem 3 --psm 6'
                    # extracted_text = pytesseract.image_to_string(Image.open(pdf_file), config=custom_config)
            except Exception as e:
                print(f"Error processing {pdf_file}: {e}")

            if self.remove_newlines_checkbox.isChecked():
                extracted_text = extracted_text.replace('\n', ' ')

            self.text_edit.setPlainText(extracted_text)

            if selected_method == "PyMuPDF + PyTesseract":
                output_folder = os.path.join(os.path.dirname(pdf_file), "invoice_extracted")
                os.makedirs(output_folder, exist_ok=True)
                output_file = os.path.join(output_folder, f"invoice_extracted_pdf_{index}.txt")
                try:
                    with open(output_file, "w") as f:
                        f.write(extracted_text)
                    print(f"Text extracted from {pdf_file} and saved to {output_file}")
                except Exception as e:
                    print(f"Error saving text to file {output_file}: {e}")



def main():
    app = QApplication(sys.argv)
    window = PDFExtractorApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
