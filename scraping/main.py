import json
import random
import time
import os
import ast
import shutil
import re
from googlegit_scraper import GoogleGitScraper
from config import base_path
from scraper_manager import ScraperManager
from semgrep_extractor import SemgrepExtractor


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

    def move_files(self, filename: str, alternative_filename: str, extension: str):
        """Moves files from the results folder to pure_java_crs."""
        source_folder = os.path.join(self.base_path, "results")
        destination_folder = os.path.join(self.base_path, filename)
        os.makedirs(destination_folder, exist_ok=True)
        pure_java = True
        i = 0

        for file in os.listdir(source_folder):
            i = i + 1
            change_request_files = self.filter_files_based_on_language(file)

            # Check if all files in change_request_files are Java files
            #pure_java = all(extension in change_request_file for change_request_file in change_request_files)
            pure_java = any(extension in change_request_file for change_request_file in change_request_files)

            # Define destination folder based on pure_java check
            destination_folder = os.path.join(self.base_path, filename if pure_java else alternative_filename)

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
            elif line.startswith("diff --git") or line.startswith('index ') or line.startswith('@@ '):
                #before_lines.append(f"//Synthetic comment -- {line}")
                #after_lines.append(f"//Synthetic comment -- {line}")
                continue
            elif line.startswith(' ') or not line.startswith(('+', '-')):
                # Common context or neutral lines
                stripped_line = line.lstrip(' ')
                before_lines.append(stripped_line)
                after_lines.append(stripped_line)

        return after_lines, before_lines

    def divide_crs (self, starting_folder: str, after_folder: str, before_folder: str, tasks_folder: str, extension: str, comment_symbol: str):
        source_folder = os.path.join(self.base_path, starting_folder)
        after_folder = os.path.join(self.base_path, after_folder)
        os.makedirs(after_folder, exist_ok=True)
        before_folder = os.path.join(self.base_path, before_folder)
        os.makedirs(before_folder, exist_ok=True)
        cr_folder = os.path.join(self.base_path, tasks_folder)
        os.makedirs(cr_folder, exist_ok=True)
        after_files = []
        before_files = []

        i = 0
        snippet_count = 0

        for file in os.listdir(source_folder):
            unformatted_files = {"CR_23099-1.json", "CR_23811-1.json", "CR_40028-1.json", "CR_45923-1.json", "CR_5158.json"}
            if file not in unformatted_files:
                print(f"Iteration number {i}, namefile: {file}")
                after_files = []
                before_files = []
                full_path = os.path.join(source_folder, file)
                try:
                    with open(full_path, "r", encoding='utf-8') as source_file:
                        source_data = json.load(source_file)

                    cr_task = source_data.get("CR task", "")
                    files = source_data.get("files", {})

                    json_cr_task = {
                        "cr_task": f"CR_TASK = {cr_task}"
                    }

                    #after_files.append([modified_cr_task])
                    #after_files.append("\n")
                    #before_files.append([modified_cr_task])
                    #after_files.append("\n")

                    snippet_count = 0
                    for file_info in files:
                        filename = file_info.get("filename", "")
                        file_content = file_info.get("file content", "")
                        # Prepare diff text by combining filename and content
                        diff_text = f"{filename}\n\n{file_content}"
                        beginning_task = f"\n{comment_symbol}<Beginning of snippet n. {snippet_count}>\n"
                        end_task = f"\n{comment_symbol}<End of snippet n. {snippet_count}>\n"
                        after_lines, before_lines = self.save_diff_versions(diff_text)
                        after_files.append([beginning_task])
                        after_files.append(after_lines)
                        after_files.append([end_task])
                        after_files.append("\n\n\n\n")
                        before_files.append([beginning_task])
                        before_files.append(before_lines)
                        before_files.append([end_task])
                        before_files.append("\n\n\n\n")
                        snippet_count = snippet_count + 1

                    before_files_flat = [item for sublist in before_files for item in sublist]
                    after_files_flat = [item for sublist in after_files for item in sublist]
                    name = file.rpartition('.')[0]
                    full_cr_path = os.path.join(cr_folder, f"cr_task_{name}.json")
                    full_before_path = os.path.join(before_folder, f"before_{name}.{extension}")
                    full_after_path = os.path.join(after_folder, f"after_{name}.{extension}")
                    # Save to files
                    with open(f"{full_before_path}", 'w', encoding='utf-8') as f_before:
                        f_before.write('\n'.join(before_files_flat))

                    with open(f"{full_after_path}", 'w', encoding='utf-8') as f_after:
                        f_after.write('\n'.join(after_files_flat))

                    with open(f"{full_cr_path}", 'w', encoding='utf-8') as cr:
                        json.dump(json_cr_task, cr, indent=4)

                    i = i + 1
                except FileNotFoundError:
                    print(f"Error: File {file} not found")

                except json.JSONDecodeError:
                    print("Error while reading the JSON file")

    def create_random_dataset(self, medium_medium_array, remaining_array, dataset_size=312, medium_sample_size=38):

        # Step 2: Randomly select 48 from medium_medium
        sampled_medium = random.sample(medium_medium_array, medium_sample_size)

        # Step 3: Combine with high_high array
        array_semgrep_before = set(sampled_medium + remaining_array)
        print(f"size of array_semgrep_before {len(array_semgrep_before)}")

        # Step 4: Load all filenames from "before_crs"
        source_folder = os.path.join(self.base_path, "Java/before_crs")
        all_files = os.listdir(source_folder)

        # Ensure we're not selecting duplicates
        valid_files = list(set(all_files) - array_semgrep_before)

        if len(valid_files) < dataset_size:
            raise ValueError("Not enough unique files to sample from.")

        dataset_files = random.sample(valid_files, dataset_size)

        # Step 5: Copy to "dataset" folder
        dataset_folder = os.path.join(self.base_path, "dataset")
        os.makedirs(dataset_folder, exist_ok=True)

        dataset_files = dataset_files + list(array_semgrep_before)

        for file_name in dataset_files:
            src = os.path.join(source_folder, file_name)
            dst = os.path.join(dataset_folder, file_name)
            shutil.copyfile(src, dst)

        return dataset_files, sampled_medium

    def list_from_file(self, array_filename):
        array_file = os.path.join(base_path, f"semgrep_names/{array_filename}.txt")
        with open(array_file, "r") as f:
            content = f.read()

        array = ast.literal_eval(content)
        array = list(array)
        return array

    def extract_cr_identifiers(self, filenames):
        pattern = re.compile(r"CR_\d+-\d+")
        identifiers = set()
        for name in filenames:
            match = pattern.search(name)
            if match:
                identifiers.add(match.group())
        return identifiers

    def copy_matching_tasks(self, dataset_folder, cr_tasks_folder, output_folder):
        os.makedirs(output_folder, exist_ok=True)

        dataset_files = os.listdir(dataset_folder)
        cr_ids = self.extract_cr_identifiers(dataset_files)

        task_files = os.listdir(cr_tasks_folder)

        for task_file in task_files:
            if any(cr_id in task_file for cr_id in cr_ids):
                src = os.path.join(cr_tasks_folder, task_file)
                dst = os.path.join(output_folder, task_file)
                shutil.copyfile(src, dst)

        print(f"Copied all matching tasks to '{output_folder}'.")

if __name__ == "__main__":
    controller = ScraperController(base_path)
    #controller.load_data()
    #controller.scrape()  # Call to start scraping
    #controller.move_files()  # Call to move files

    #controller.divide_crs("python_crs", "after_python_crs", "before_python_crs", "cr_python_tasks", "py", "#")
    #controller.move_files("python_crs", "no_python_crs", ".py")

    filename = "semgrep_medium_low"
    filename_pos = "positions"
    semgrep_file = os.path.join(base_path, f"semgrep_csv/{filename}.csv")
    extractor = SemgrepExtractor(semgrep_file)
    names = extractor.get_unique_names()

    #print(len(extractor.names))
    #print(names)
    #print(len(names))

    #semgrep_names = os.path.join(base_path, f"semgrep_names/{filename}.txt")
    #with open(semgrep_names, "w") as file:
        #file.write(f"Number of files: {len(names)} \n\n {names}")

    high_high_array = controller.list_from_file("semgrep_high_high")
    high_medium_array = controller.list_from_file("semgrep_high_medium")
    medium_high_array = controller.list_from_file("semgrep_medium_high")
    medium_medium_array = controller.list_from_file("semgrep_medium_medium")
    medium_low_array = controller.list_from_file("semgrep_medium_low")

    remaining_array = (high_high_array + high_medium_array + medium_high_array + medium_low_array)

    dataset, sample_medium = controller.create_random_dataset(medium_medium_array, remaining_array)

    print(f"Dataset of {len(dataset)} files created in 'dataset/' folder.")
    print(f"Sample of medium medium vulnerabilities: {len(sample_medium)}.")

    dataset_folder = os.path.join(base_path, "dataset")
    cr_tasks_folder = os.path.join(base_path, "Java/cr_tasks")
    output_folder = os.path.join(base_path, "matching_cr_tasks")

    controller.copy_matching_tasks(dataset_folder, cr_tasks_folder, output_folder)