from googlegit_scraper import GoogleGitScraper
from scraper.config import base_path

# Hardcoded values
review_id = "51750"
project = "platform/packages/apps/Settings"
git_revision = "ca714d8d0c11c904b25bc20a0a9b2f2cc8d78ad5"

# URL construction
base_url = "https://android.googlesource.com/"
project_url = f"{base_url}{project}/+/{git_revision}%5E%21/"

# Execute the function
scraper = GoogleGitScraper(project_url, base_path)
diff_tags, unified_diff_tags, content = scraper.fetch_and_save_diffs_with_filenames()
scraper.save_into_file(diff_tags, unified_diff_tags, content, review_id)