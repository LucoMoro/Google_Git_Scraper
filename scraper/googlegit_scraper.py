import requests
from bs4 import BeautifulSoup

class GoogleGitScraper:
    def __init__(self, url, output_path):
        self.url = url
        self.output_path = output_path

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

            if diff_tags and unified_diff_tags:
                # Open the output file for writing
                with open(self.output_path, "w", encoding="utf-8") as file:
                    for diff_tag, unified_diff_tag in zip(diff_tags, unified_diff_tags):
                        # Extract the filename from the Diff tag
                        filename = diff_tag.text.strip()

                        # Write filename and corresponding diff to the output file
                        file.write(f"--- Task: {content} ---\n")
                        file.write(f"--- File: {filename} ---\n")
                        file.write(unified_diff_tag.text)
                        file.write("\n\n")
                print(f"All diffs saved to: {self.output_path}")
            else:
                print("No matching tags found for filenames or diffs.")

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
