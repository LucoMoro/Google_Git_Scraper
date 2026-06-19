import os
import pandas as pd

class ScraperManager:
    def __init__(self, path: str):
        self.path = path

    def open_excel(self):
        full_path = os.path.join(self.path, "dataset_google_git.xlsx")
        data_frame = pd.read_excel(full_path, usecols=["ReviewId", "Project", "PatchSetId", "GitRevision"], engine="openpyxl")

        ids = data_frame["ReviewId"].to_list()
        projects = data_frame["Project"].to_list()
        patchs = data_frame["PatchSetId"].to_list()
        revisions = data_frame["GitRevision"].to_list()

        return ids, projects, patchs, revisions