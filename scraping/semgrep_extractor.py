import csv
import re

class SemgrepExtractor:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.rows = []
        self.names = []

    def read_row(self) -> None:
        with open(self.csv_file, newline='') as file:
            self.rows = csv.reader(file, delimiter=',')

            for row in self.rows:
                for column in row:
                    #after_pattern = r'/after_crs/(after_CR_.*?)(?:#|$)'
                    #after_match = re.search(after_pattern, column)
                    before_pattern = r'/before_crs/(before_CR_.*?)(?:#|$)'
                    before_match = re.search(before_pattern, column)
                    #if after_match:
                        #self.names.append(after_match.group(1))
                    if before_match:
                        self.names.append(before_match.group(1))

    def get_unique_names(self):
        self.read_row()
        set_names = set(self.names)
        return set_names

    def get_rows(self):
        return self.rows