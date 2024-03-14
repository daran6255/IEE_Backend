# from PIL import Image
# import pytesseract
# import pandas as pd
# from tabulate import tabulate

# img = Image.open('data/dataset/train_data/1.jpg')
# text = pytesseract.image_to_string(img)
# lines = text.split('\n')
# data = [line.split() for line in lines]
# df = pd.DataFrame(data)

# print(tabulate(df, headers='keys', tablefmt='psql'))

import tabula  
# address of the file  
myfile = 'temp/invoice_converted_5.pdf'  
# using the read_pdf() function  
mytable = tabula.read_pdf(myfile, pages = 1, multiple_tables = True)  
# printing the table  
print(mytable)  
# print(mytable[1])  