from googlegit_scraper import GoogleGitScraper

# Hardcoded values
review_id = "51750"
project = "platform/packages/apps/Settings"
git_revision = "ca714d8d0c11c904b25bc20a0a9b2f2cc8d78ad5"

# URL construction
base_url = "https://android.googlesource.com/"
project_url = f"{base_url}{project}/+/{git_revision}%5E%21/"
output_file = "modified_files_diff.txt"

# Execute the function
scraper = GoogleGitScraper(project_url, output_file)
scraper.fetch_and_save_diffs_with_filenames()