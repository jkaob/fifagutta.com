from .scraper import ScheduleScraper


class Kampspill():
    def __init__(self, year) -> None:
        self.year = year
        self.scraper = ScheduleScraper()

    def get_next_matches(self, n_days=7, verbose=False):
        return self.scraper.get_next_match_elements(n_days, 0.0, verbose=verbose)

    def get_past_matches(self, verbose=False):
        return self.scraper.get_past_match_elements(verbose=verbose)