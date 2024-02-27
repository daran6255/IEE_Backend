#Step 1: text cleaning
            # special charecters, puntucations marks, charecter symbols,
#Step 2: Tokenization
            # Split the text into individual tokens, such as words or numbers.
#Step 3: Normalization
            # Convert tokens to a standard format such as lowercase.
#Step 4: Date_standardization
            # Extract and standardize date formats from the invoice to (dd-mm-yyy).

text_clean(invoice)
    # remove non alpha numeric charecteres
    # remove extra white spaces
    # include dots

text_tokenizer(output1)
    # split text into individual tokens

text_normalization(output2)
    # convert text to lower case

date_standardization(output3)
    # convert dates to standarded format (dd/mm/yyyy)


for invoice in invoice_ocr folder(index)
    output1 = text_clean (invoice)
    output2 = text_tokenizer(output1)
    output3 = text_normalization(output2)
    output4 = date_standardization(output3)

    # save final output to final_text_annotations.txt
    # array of strings - Tokanization output
    # index - final_text_annotations{index}.txt
        