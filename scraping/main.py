import json
import random
import time
import os
from googlegit_scraper import GoogleGitScraper
from config import base_path
from scraper_manager import ScraperManager


class ScraperController:
    def __init__(self, base_path, max_retries=3):
        self.base_path = base_path
        self.max_retries = max_retries
        self.scraping_manager = ScraperManager(base_path)
        self.base_url = "https://android.googlesource.com/"
        self.ids = []
        self.projects = []
        self.patches = []
        self.revisions = []


    def load_data(self):
        """Loads data from the Excel file."""
        self.ids, self.projects, self.patches, self.revisions = self.scraping_manager.open_excel()

    def scrape(self, start=1, end=3):
        """Runs the scraping process for a given range."""
        for i in range(start, end):
            sleep_time = random.uniform(5, 10)
            time.sleep(sleep_time)

            current_id = self.ids[i]
            current_project = self.projects[i]
            current_patch = self.patches[i]
            current_revision = self.revisions[i]
            project_url = f"{self.base_url}{current_project}/+/{current_revision}%5E%21/"

            print(f"Iteration number: {i}")
            scraper = GoogleGitScraper(project_url, self.base_path)
            retries = 0
            success = False

            while retries < self.max_retries and not success:
                try:
                    if retries != 0:
                        time.sleep(30)

                    diff_tags, unified_diff_tags, content = scraper.fetch_and_save_diffs_with_filenames()
                    scraper.save_into_file(diff_tags, unified_diff_tags, content, current_patch)
                    success = True  # Mark as successful if no error occurs
                except Exception as e:
                    retries += 1
                    if retries == self.max_retries:
                        with open('errors.txt', 'a') as error_file:
                            error_file.write(f"{i}\n")
                        break  # Move to the next iteration

    def move_files(self):
        """Moves files from the results folder to pure_java_crs."""
        source_folder = os.path.join(self.base_path, "results")
        destination_folder = os.path.join(self.base_path, "pure_java_crs")
        os.makedirs(destination_folder, exist_ok=True)
        pure_java = True
        i = 0

        for file in os.listdir(source_folder):
            i = i + 1
            change_request_files = self.filter_files_based_on_language(file)

            # Check if all files in change_request_files are Java files
            pure_java = all('.java' in change_request_file for change_request_file in change_request_files)

            # Define destination folder based on pure_java check
            destination_folder = os.path.join(self.base_path, "pure_java_crs" if pure_java else "no_java_crs")

            # Ensure the destination folder exists
            os.makedirs(destination_folder, exist_ok=True)

            # Move the file
            file_path = os.path.join(source_folder, file)
            if os.path.isfile(file_path):
                os.rename(file_path, os.path.join(destination_folder, file))
            print(f"Iteration on moving files: {i}")

        print("Files moved successfully.")

    def filter_files_based_on_language(self, file):
        file_path = os.path.join(self.base_path, f"results/{file}")
        try:
            with open(file_path, "r") as change_request:
                change_request_data = json.load(change_request)

                changed_files = change_request_data.get("files", {})
                filenames = [changed_file["filename"].split(" ")[2] for changed_file in changed_files]

            return filenames
        except FileNotFoundError:
            print(f"Error: File {file_path} not found")
        except json.JSONDecodeError:
            print("Error while reading the JSON file")

    def save_diff_versions(self, diff_text):
        before_lines = []
        after_lines = []

        for line in diff_text.splitlines():
            if line.startswith('+') and not line.startswith('+++'):
                after_lines.append(line[1:])
            elif line.startswith('-') and not line.startswith('---'):
                before_lines.append(line[1:])  # Remove '-' prefix
            elif line.startswith(' ') or not line.startswith(('+', '-')):
                # Common context or neutral lines
                stripped_line = line.lstrip(' ')
                before_lines.append(stripped_line)
                after_lines.append(stripped_line)

        return after_lines, before_lines

    def divide_crs (self):
        source_folder = os.path.join(self.base_path, "pure_java_crs")
        after_folder = os.path.join(self.base_path, "after_crs")
        os.makedirs(after_folder, exist_ok=True)
        before_folder = os.path.join(self.base_path, "before_crs")
        os.makedirs(before_folder, exist_ok=True)
        after_files = []
        before_files = []

        for file in os.listdir(source_folder):
            full_path = os.path.join(source_folder, file)
            try:
                with open(full_path, "r") as source_file:
                    source_data = json.load(source_file)

                cr_task = source_data.get("CR task", {})
                files = source_data.get("files", {})

                for file_info in files:
                    filename = file_info.get("filename", "")
                    file_content = file_info.get("file content", "")
                    # Prepare diff text by combining filename and content
                    diff_text = f"{filename} \n\n {file_content}"
                    after_lines, before_lines = self.save_diff_versions(diff_text)
                    after_files.append(after_lines)
                    before_files.append(before_lines)

                before_files_flat = [item for sublist in before_files for item in sublist]
                after_files_flat = [item for sublist in after_files for item in sublist]
                full_before_path = os.path.join(before_folder, file)
                full_after_path = os.path.join(after_folder, file)
                # Save to files
                with open(f"{full_before_path}", 'w') as f_before:
                    f_before.write('\n'.join(before_files_flat))

                with open(f"{full_after_path}", 'w') as f_after:
                    f_after.write('\n'.join(after_files_flat))


            except FileNotFoundError:
                print(f"Error: File {file} not found")

            except json.JSONDecodeError:
                print("Error while reading the JSON file")


if __name__ == "__main__":
    controller = ScraperController(base_path)
    #controller.load_data()
    #controller.scrape()  # Call to start scraping
    #controller.move_files()  # Call to move files

    controller.divide_crs()

