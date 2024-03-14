import pandas as pd
import json

# Sample JSON data
data_json = '''
{
  "requestId": "d287c886-9905-44fb-866f-86fded31f995",
  "result": [
    {
      "enitites": {
        "AMOUNT": [
          "450.00",
          "183.00",
          "175.00",
          "360.00",
          "360.00",
          "150.00",
          "180.00"
        ],
        "CGSTIN": [
          "29aalcro358l1zu"
        ],
        "CUSTOMER": [
          "rawgranules private limit-"
        ],
        "HSN": [
          "09109100",
          "09109100",
          "09109100",
          "09109100",
          "09109100",
          "09109100",
          "21039010"
        ],
        "INVOICEDATE": [
          "14/07/2023"
        ],
        "INVOICENO": [
          "atl-1166"
        ],
        "ITEMNAME": [
          "teju sprgrm msl 200gm",
          "teju 25gm chi/msl 10/-",
          "teju egg/msl10/-",
          "teiu chi mtn bryn 20gm 10/-",
          "teju veg plv pdr 20gm 10/-",
          "teju puliyogre 10/-",
          "teju ggp 70gm 10/-"
        ],
        "PRICE": [
          "225.00",
          "183.00",
          "17500",
          "72.00",
          "72.00",
          "75.00",
          "180.00"
        ],
        "QUANTITY": [
          "2.00/kgs.",
          "1.00",
          "1.00",
          "5.00",
          "5.00",
          "2.00",
          "1.00"
        ],
        "TAXABLEAMT": [
          "1758.82"
        ],
        "UNIT": [
          "sheet",
          "sheet",
          "sheet",
          "sheet",
          "sheet",
          "sheet"
        ],
        "VENDOR": [
          "adithya trade links"
        ],
        "VGSTIN": [
          "29cxbpk6398h1zw"
        ]
      },
      "filename": "D  14-07 IN 1166 - INR 1858.jpg"
    }
  ]
}
'''

# Load JSON data
data = json.loads(data_json)

# Extract entities from the first result
entities = data['result'][0]['enitites']

# Find the maximum length among all arrays
max_length = max(len(arr) for arr in entities.values())

# Pad arrays with fewer elements with a placeholder value (e.g., '')
padded_entities = {key: arr + [''] * (max_length - len(arr)) for key, arr in entities.items()}

# Create DataFrame from the padded entities
df = pd.DataFrame(padded_entities)

# Write DataFrame to Excel file
excel_file = 'entities_data.xlsx'
df.to_excel(excel_file, index=False)

print(f"DataFrame has been written to '{excel_file}' successfully.")
