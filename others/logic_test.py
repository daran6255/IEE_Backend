def map_items(mapped_headings, items_output, items_itags, entities_output):
    indices = {tag: items_output[0].index(mapped_headings.get(tag))
               if mapped_headings.get(tag) and mapped_headings.get(tag) != 'N.E.R.Default' else None for tag in items_itags}

    final_dict = {tag: [{'value': items_output[i][indices[tag]]} if indices[tag] is not None
                        else {'value': entities_output[tag][i-1]} if mapped_headings.get(tag) == 'N.E.R.Default'
                        else {'value': ''} for i in range(1, len(items_output))]
                  for tag in items_itags}

    return final_dict


mapped_headings = {'ITEMNAME': ' Description of Goods', 'HSN': 'N.E.R.Default',
                   'QUANTITY': ' Quantity', 'UNIT': None, 'PRICE': ' Rate', 'AMOUNT': ' Amount'}
items_output = [[' Si to', ' Description of Goods', ' HSN/SAC', ' Quantity', ' Rate (Incl. of Tax)', ' Rate', ' per', ' Amount'], [' 1', ' Shubhra Floor Cleaner', ' 3402', ' 5 No', ' 249.99', ' 211.86', ' No', ' 1,059.30'], [
    ' 2', ' 5 Lit Can 2 Shubhra Multipurpose Can', ' 3402', ' 5 No', ' 200.00', ' 169.49', ' No', ' 847.45'], ['N/A', ' Cleaner 5 Lit', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', ' 1,906.75']]
items_itags = ['ITEMNAME', 'HSN', 'QUANTITY', 'UNIT', 'PRICE', 'AMOUNT']
entities_output = {'VENDOR': ['sriranga enterprises'], 'INVOICEDATE': ['10/08/2023'], 'VGSTIN': ['29ahupa9347d1zz'], 'CUSTOMER': ['rawgranules private limited'], 'CGSTIN': ['29aalcr0358l1zu'], 'ITEMNAME': ['shubhra floor cleaner',
                                                                                                                                                                                                              'shubhra multipurpose'], 'HSN': ['9999', '9999', '1234'], 'QUANTITY': ['5', '5'], 'UNIT': ['no', 'no', 'no', 'no', 'cleaner', 'can'], 'PRICE': ['211.86', '169.49'], 'AMOUNT': ['1059.30', '847.45', '1906.75'], 'GRANDTOTAL': ['2250.00']}
print(map_items(mapped_headings, items_output, items_itags, entities_output))
