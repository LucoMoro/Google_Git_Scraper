from googlegit_scraper import GoogleGitScraper
from scraping.config import base_path
from scraping.scraper_manager import ScraperManager

# Hardcoded values
#review_id = "51750"
#project = "platform/packages/apps/Settings"
#git_revision = "ca714d8d0c11c904b25bc20a0a9b2f2cc8d78ad5"
#project_url = f"{base_url}{project}/+/{git_revision}%5E%21/"

scraping_manager = ScraperManager(base_path)
ids, projects, patches, revisions = scraping_manager.open_excel()

# URL construction
base_url = "https://android.googlesource.com/"

# Execute the function
for i in range(0, 10):
    current_id = ids[i]
    current_project = projects[i]
    current_patch = patches[i]
    current_revision = revisions[i]
    project_url = f"{base_url}{current_project}/+/{current_revision}%5E%21/"
    scraper = GoogleGitScraper(project_url, base_path)
    diff_tags, unified_diff_tags, content = scraper.fetch_and_save_diffs_with_filenames()
    scraper.save_into_file(diff_tags, unified_diff_tags, content, current_patch)