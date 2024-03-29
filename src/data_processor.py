import re
from fuzzywuzzy import process
from spellchecker import SpellChecker


class DataProcessor:
    spell = SpellChecker()

    def __init__(self, keywords=None):
        self.keywords = keywords

    def apply_keywords_matching(self, data, keywords):
        for column, keywords in keywords.items():
            if not self.result[column]:
                for keyword in keywords:
                    if keyword in data:
                        self.result[column] = keyword
                        break

    def apply_named_entity_recognition(self, table, ner_output):
        for key, value in self.result.items():
            if key in ner_output:
                if value is None:
                    for i in range(len(table[0])):  # iterate over each column
                        if set(table[j][i] for j in range(1, len(table))).intersection(set(ner_output[key])):
                            self.result[key] = table[0][i]
                            break
                else:
                    idx = table[0].index(value)
                    column_values = [row[idx] for row in table[1:]]
                    if all(val == "N/A" for val in column_values) and len(column_values) == len(ner_output.get(key, [])):
                        self.result[key] = "N.E.R.Default"

    def apply_fuzzy_matching(self, data):
        # for column, value in result.items():
        #     if not value:
        #         extracted_column, confidence = process.extractOne(column, data)
        #         result[column] = extracted_column if extracted_column in data else None

        self.temp_result = dict(sorted(self.result.items()))
        used = set(value for value in self.temp_result.values() if value)

        for column in self.temp_result.keys():
            if not self.result[column]:
                matches = process.extract(column, data, limit=len(data))
                for match, confidence in matches:
                    if match not in used and confidence >= 50:
                        used.add(match)
                        self.result[column] = match
                        break

    def apply_spell_correct_matching(self, data, keywords):
        # corrected_data = []

        # for s in data:
        #     corrected = self.spell.correction(s)
        #     corrected_data.append(corrected if corrected else s)

        for column, values in keywords.items():
            if not self.result[column]:
                for value in values:
                    for item in data:
                        if re.search(value, item, re.IGNORECASE):
                            self.result[column] = item

                    # if not self.result[column]:
                    #     for idx, item in enumerate(corrected_data):
                    #         if re.search(value, item, re.IGNORECASE):
                    #             self.result[column] = data[idx]

    def process_table_data(self, table, ner_output=None):
        if self.keywords is None:
            print('Please provide Keywords for Table Data')
            return

        self.result = {}
        headings = table[0]

        original_to_preprocessed = {re.sub(
            r'[^a-zA-Z0-9\s.]', ' ', item): item for item in headings}

        heading_mapping = {
            re.sub(r'[^a-zA-Z0-9\s.]', ' ', item): item for item in headings}

        final_headings = [
            heading for heading in heading_mapping if heading != "N A"]

        self.result = {key: None for key in self.keywords.keys()}

        self.apply_keywords_matching(final_headings, self.keywords)
        if ner_output:
            self.apply_named_entity_recognition(table, ner_output)
        self.apply_spell_correct_matching(final_headings, self.keywords)
        self.apply_fuzzy_matching(final_headings)

        # Map the results back to the original headings
        self.result = {key: original_to_preprocessed.get(
            value, value) for key, value in self.result.items()}

        return self.result
