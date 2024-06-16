import re
from fuzzywuzzy import process
from spellchecker import SpellChecker


class DataProcessor:
    spell = SpellChecker()

    def __init__(self, keywords=None):
        self.keywords = keywords

    def apply_keywords_matching(self, data, keywords):
        for column, keywords_data in keywords.items():
            if not self.result[column]:
                for keyword in keywords_data:
                    if keyword in data and data[keyword] not in self.result.values():
                        self.result[column] = data[keyword]
                        break

    def apply_named_entity_recognition(self, table, ner_output):
        for key, value in self.result.items():
            if key in ner_output:
                if value is None:
                    # iterate over each column
                    for idx in range(len(table[0])):
                        column_words_set = set(word for j in range(
                            1, len(table)) for word in table[j][idx].split())
                        ner_words_set = set(
                            word for phrase in ner_output[key] for word in phrase.split())
                        intersection = column_words_set.intersection(
                            ner_words_set)

                        if intersection:
                            match_percentage = len(
                                intersection) / min(len(column_words_set), len(ner_words_set)) * 100
                            if match_percentage > 50 and idx not in self.result.values():
                                self.result[key] = idx
                                break

                else:
                    idx = table[0].index(value)
                    column_values = [row[idx] for row in table[1:]]
                    if all(val == "N/A" for val in column_values) and len(column_values) == len(ner_output.get(key, [])):
                        # Set -1 for this entity to use NER result if all table values for this column are N/A
                        self.result[key] = -1

    def apply_spell_correct_matching(self, data, keywords):
        # corrected_data = []

        # for s in data:
        #     corrected = self.spell.correction(s)
        #     corrected_data.append(corrected if corrected else s)

        for column, values in keywords.items():
            if not self.result[column]:
                found_match = False
                for value in values:
                    for item in data:
                        if re.search(value, item, re.IGNORECASE) and data[item] not in self.result.values():
                            found_match = True
                            self.result[column] = data[item]
                            break

                    if found_match:
                        break

                    # if not self.result[column]:
                    #     for idx, item in enumerate(corrected_data):
                    #         if re.search(value, item, re.IGNORECASE):
                    #             self.result[column] = data[idx]

    def apply_fuzzy_matching(self, data):
        # for column, value in result.items():
        #     if not value:
        #         extracted_column, confidence = process.extractOne(column, data)
        #         result[column] = extracted_column if extracted_column in data else None

        self.temp_result = dict(sorted(self.result.items()))

        for column in self.temp_result.keys():
            if not self.result[column]:
                matches = process.extract(
                    column, list(data.keys()), limit=len(data))
                for match, confidence in matches:
                    if confidence >= 50 and data[match] not in self.result.values():
                        self.result[column] = data[match]
                        break

    def process_table_data(self, table, ner_output=None):
        if self.keywords is None:
            print('Please provide Keywords for Table Data')
            return

        self.result = {}
        headings = table[0]

        # Convert all data to lowercase
        new_keywords = {key: [word.lower() for word in words_list]
                        for key, words_list in self.keywords.items()}
        new_table = [[s.lower() for s in sub_array] for sub_array in table]

        final_headings = {re.sub(
            r'[^a-zA-Z0-9\s.]', ' ', item): idx for idx, item in enumerate(headings) if item != "N/A"}

        self.result = {key: None for key in new_keywords.keys()}

        self.apply_keywords_matching(final_headings, new_keywords)
        if ner_output:
            self.apply_named_entity_recognition(new_table, ner_output)
        self.apply_spell_correct_matching(final_headings, new_keywords)
        self.apply_fuzzy_matching(final_headings)

        return self.result
