from scraper.scraper_controller import ScraperController
from config import base_path

def main():
    controller = ScraperController(base_path)
    controller.load_data()
    controller.scrape()  # Call to start scraping

    controller.divide_crs("java_crs", "after_java_crs", "before_java_crs", "cr_java_tasks", "java", "#")
    controller.move_files("java_crs", "no_java_crs", ".java")
