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

    def create_random_dataset(self, array1, array2, dataset_size=338, medium_sample_size=19):

        # Step 2: Randomly select 48 from medium_medium
        sampled_medium = random.sample(array1, medium_sample_size)

        # Step 3: Combine with high_high array
        array_semgrep_before = set(sampled_medium + array2)
        print(f"size of array_semgrep_before {len(array_semgrep_before)}")

        # Step 4: Load all filenames from "before_crs"
        source_folder = os.path.join(self.base_path, "snippets_corti_2000")
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

    def filter_existing_files(self, filenames, folder_path):
        """
        Takes a list of filenames and returns a filtered list
        containing only those that exist in the given folder.

        Args:
            filenames (list): List of file names (with or without extensions).
            folder_path (str): Path to the folder where files are expected.

        Returns:
            list: Filtered list containing only filenames that exist in the folder.
        """
        existing_files = []
        for name in filenames:
            file_path = os.path.join(folder_path, name)
            if os.path.isfile(file_path):
                existing_files.append(name)
        return existing_files

    def from_before_take_after(self):
        before_files = []
        before_path = os.path.join(base_path, "dataset//snippets")
        for before_file in os.listdir(before_path):
            before_name, _ = os.path.splitext(before_file)
            filtered_name = before_name.replace("before_", "")
            before_files.append(filtered_name)

        after_path = os.path.join(base_path, "Java//after_crs")
        after_dataset = os.path.join(base_path, "after_dataset")
        for name in before_files:
            src = os.path.join(after_path, f"after_{name}.java")
            dst = os.path.join(after_dataset, f"after_{name}.java")
            shutil.copyfile(src, dst)


    def main(self, controller):
        # controller.load_data()
        # controller.scrape()  # Call to start scraping
        # controller.move_files()  # Call to move files

        # controller.divide_crs("python_crs", "after_python_crs", "before_python_crs", "cr_python_tasks", "py", "#")
        # controller.move_files("python_crs", "no_python_crs", ".py")

        filename = "semgrep_medium_low"
        filename_pos = "positions"
        semgrep_file = os.path.join(base_path, f"semgrep_csv/{filename}.csv")
        extractor = SemgrepExtractor(semgrep_file)
        names = extractor.get_unique_names()

        # print(len(extractor.names))
        # print(names)
        # print(len(names))

        semgrep_names = os.path.join(base_path, f"semgrep_names/{filename}.txt")
        with open(semgrep_names, "w") as file:
            file.write(f"{names}")

        high_high_array = controller.list_from_file("semgrep_high_high")
        high_medium_array = controller.list_from_file("semgrep_high_medium")
        medium_high_array = controller.list_from_file("semgrep_medium_high")
        medium_medium_array = controller.list_from_file("semgrep_medium_medium")
        medium_low_array = controller.list_from_file("semgrep_medium_low")

        filtered_dataset_path = os.path.join(base_path, "snippets_corti_2000")
        high_high_array_filtered = controller.filter_existing_files(high_high_array, filtered_dataset_path)
        high_medium_array_filtered = controller.filter_existing_files(high_medium_array, filtered_dataset_path)
        medium_high_array_filtered = controller.filter_existing_files(medium_high_array, filtered_dataset_path)
        medium_low_array_filtered = controller.filter_existing_files(medium_low_array, filtered_dataset_path)
        medium_medium_array_filtered = controller.filter_existing_files(medium_medium_array, filtered_dataset_path)

        remaining_array_filtered = (
                    high_high_array_filtered + high_medium_array_filtered + medium_high_array_filtered + medium_low_array_filtered)

        print(f"high high {len(high_high_array)}")
        print(f"high medium {len(high_medium_array)}")
        print(f"medium high {len(medium_high_array)}")
        print(f"medium low {len(medium_low_array)}")
        print(f"medium medium {len(medium_medium_array)}")

        print(f"high high {high_high_array_filtered}")
        print(f"high medium {high_medium_array_filtered}")
        print(f"medium high {medium_high_array_filtered}")
        print(f"medium low {medium_low_array_filtered}")
        print(f"medium medium {medium_medium_array_filtered}")

        dataset, sample_medium = controller.create_random_dataset(medium_medium_array_filtered,
                                                                  remaining_array_filtered)

        print(f"Dataset of {len(dataset)} files created in 'dataset/' folder.")
        print(f"Sample of medium medium vulnerabilities: {len(sample_medium)}.")

        dataset_folder = os.path.join(base_path, "dataset")
        cr_tasks_folder = os.path.join(base_path, "Java/cr_tasks")
        output_folder = os.path.join(base_path, "matching_cr_tasks")

        controller.copy_matching_tasks(dataset_folder, cr_tasks_folder, output_folder)

    def folders_exploration(self):
        root_dir = os.path.join(base_path, "configuration_results//configuration_1")
        conversation_change_map = {}

        for conversation in sorted(os.listdir(root_dir)):
            conv_path = os.path.join(root_dir, conversation)
            if not os.path.isdir(conv_path):
                continue

            iterations = []
            for item in os.listdir(conv_path):
                if item.startswith("iteration_"):
                    iter_path = os.path.join(conv_path, item)
                    if os.path.isdir(iter_path):
                        #Searches change_CR_*.json
                        for fname in os.listdir(iter_path):
                            if fname.startswith("change_CR_") and fname.endswith(".json"):
                                iterations.append((int(item.split("_")[1]), os.path.join(iter_path, fname)))

            if iterations:
                #Takes the last iteration (the one with the higher number)
                last_iter = sorted(iterations, key=lambda x: x[0])[-1]
                conversation_change_map[conversation] = last_iter

        #for conv, (iter_num, path) in conversation_change_map.items():
            #print(f"{conv} -> iteration_{iter_num}: {path}")
        return conversation_change_map

    def save_changes(self, conversation_change_map):
        outcome_dir = os.path.join(base_path, "outcome_dataset")

        os.makedirs(outcome_dir, exist_ok=True)

        for conv, (_, change_path) in conversation_change_map.items():
            # Extracts the number from the folder conversation_x
            conv_id = re.search(r'\d+', conv).group()

            filename = os.path.basename(change_path)
            cr_match = re.search(r'(CR_\d+-\d+)', filename)
            cr_id = cr_match.group(1) if cr_match else "CR_unknown"

            with open(change_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    response_list = data.get("response", [])
                    if not response_list:
                        print(f"[WARN] No response in {change_path}")
                        continue
                    code_content = response_list[0].get("content", "").strip()
                    if code_content.startswith("```java"):
                        code_content = code_content.split('\n', 1)[1]
                    if code_content.endswith("```"):
                        code_content = code_content.rsplit('\n', 1)[0]

                    if not code_content:
                        print(f"[WARN] No content in {change_path}")
                        continue

                    # Creates the output directory
                    target_dir = os.path.join(outcome_dir, f"configuration_{conv_id}")
                    os.makedirs(target_dir, exist_ok=True)

                    #Saves the code in a file
                    output_path = os.path.join(target_dir, f"response_{cr_id}.java")
                    with open(output_path, 'w', encoding='utf-8') as outf:
                        outf.write(code_content)

                    print(f"[OK] Saved: {output_path}")

                except Exception as e:
                    print(f"[ERROR] Error in {change_path}: {e}")


if __name__ == "__main__":
    controller = ScraperController(base_path)
    #controller.main(controller)

    #controller.from_before_take_after()

    files_map = controller.folders_exploration()

    controller.save_changes(files_map)