import requests
from bs4 import BeautifulSoup

# Hardcoded values
review_id = "51750"
project = "platform/packages/apps/Settings"
git_revision = "ca714d8d0c11c904b25bc20a0a9b2f2cc8d78ad5"

# URL construction
base_url = "https://android.googlesource.com/"
project_url = f"{base_url}{project}/+/{git_revision}%5E%21/"
output_file = "modified_files_diff.txt"


# Function to fetch and save diffs
def fetch_and_save_diffs_with_filenames(url, output_path):
    try:
        response = requests.get(url)
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
            with open(output_path, "w", encoding="utf-8") as file:
                for diff_tag, unified_diff_tag in zip(diff_tags, unified_diff_tags):
                    # Extract the filename from the Diff tag
                    filename = diff_tag.text.strip()

                    # Write filename and corresponding diff to the output file
                    file.write(f"--- Task: {content} ---\n")
                    file.write(f"--- File: {filename} ---\n")
                    file.write(unified_diff_tag.text)
                    file.write("\n\n")
            print(f"All diffs saved to: {output_path}")
        else:
            print("No matching tags found for filenames or diffs.")

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")


# Execute the function
fetch_and_save_diffs_with_filenames(project_url, output_file)
