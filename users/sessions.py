from django.contrib.sessions.backends.db import SessionStore as DBStore

from barriers.models import Watchlist

from utils.api_client import MarketAccessAPIClient


class SessionStore(DBStore):
    """
    Custom Session Engine with convenience functions for user data
    """
    def get_watchlists(self):
        try:
            watchlists = self['user_data']['user_profile']['watchList'].get(
                'lists', []
            )
            return [Watchlist(**watchlist) for watchlist in watchlists]
        except KeyError:
            return []

    def get_watchlist(self, index):
        watchlists = self.get_watchlists()
        try:
            return watchlists[int(index)]
        except IndexError:
            return None

    def set_watchlists(self, watchlists):
        self['user_data']['user_profile']['watchList']['lists'] = [
            watchlist.to_dict() for watchlist in watchlists
        ]
        client = MarketAccessAPIClient(self['sso_token'])
        client.users.patch(user_profile=self['user_data']['user_profile'])
        self.save()

    def update_watchlist(self, index, watchlist):
        watchlists = self.get_watchlists()
        watchlists[index] = watchlist
        self.set_watchlists(watchlists)

    def rename_watchlist(self, index, name):
        watchlists = self.get_watchlists()
        if index < len(watchlists):
            watchlists[index].name = name
            self.set_watchlists(watchlists)

    def delete_watchlist(self, index):
        watchlists = self.get_watchlists()
        if index < len(watchlists):
            del watchlists[index]
            self.set_watchlists(watchlists)