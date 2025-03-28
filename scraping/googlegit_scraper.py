import requests
import os
from bs4 import BeautifulSoup
import json

class GoogleGitScraper:
    def __init__(self, url, base_path):
        self.url = url
        self.base_path = base_path

    # Function to fetch and save diffs
    def fetch_and_save_diffs_with_filenames(self):
        try:
            response = requests.get(self.url)
            response.raise_for_status()  # Check for HTTP errors

            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")
            diff_tags = soup.find_all("pre", class_="u-pre u-monospace Diff")
            unified_diff_tags = soup.find_all("pre", class_="u-pre u-monospace Diff-unified")
            cr_tasks = soup.find_all("pre", class_="u-pre u-monospace MetadataMessage")
            content = ""
            for cr_task in cr_tasks:
                content = cr_task.get_text(strip=True)

            return diff_tags, unified_diff_tags, content
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")


    def save_into_file(self, diff_tags, unified_diff_tags, content, review_id):
        cr_files = []

        if diff_tags and unified_diff_tags and content:
            # Open the output file for writing
            full_path = os.path.join(self.base_path, "results")
            output_file = os.path.join(full_path, f"CR_{review_id}.json")

            for diff_tag, unified_diff_tag in zip(diff_tags, unified_diff_tags):
                filename = diff_tag.text.strip()
                single_file = {
                    "filename": filename,
                    "file content": unified_diff_tag.text
                }
                cr_files.append(single_file)

            data = {
                "CR task": content,
                "files": cr_files
            }

            with open(output_file, "w") as output:
                json.dump(data, output, indent=4)