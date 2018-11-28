import html
import os
from collections import deque

import pickle

from pickle import PickleError


class User:
    def __init__(self, name, identifier):
        self._name = name
        self._identifier = identifier

    def __eq__(self, other):
        return isinstance(other, User) and self._identifier == other.get_identifier()

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return str.format("{0} (ID: {1})", self._name, self._identifier)

    def __hash__(self):
        return hash(self._identifier)

    def get_name(self):
        return self._name

    def update_name(self, name):
        self._name = name

    def get_identifier(self):
        return self._identifier


class BranchQueue:
    def __init__(self):
        self.users_queue = deque()
        self.active_user = None
        self.subscriptions = set()


class BotModel:
    USERS_PICKLE_FILENAME = "bot_users.pkl"
    QUEUE_PICKLE_FILENAME = "bot_queue.pkl"

    def __init__(self, config, backup_path=".", restore=False):
        self._users_pickle_file = os.path.join(backup_path, self.USERS_PICKLE_FILENAME)
        self._queue_pickle_file = os.path.join(backup_path, self.QUEUE_PICKLE_FILENAME)
        if restore:
            self._restore_users()
            self._restore_branches(config)
        else:
            self._user_infos = {}
            self._branches = {}

        for branch in config.get_branches():
            if branch not in self._branches:
                self._branches[branch] = BranchQueue()

    def _restore_users(self):
        if os.path.exists(self._users_pickle_file):
            try:
                pkl_file = open(self._users_pickle_file, 'rb')
                self._user_infos = pickle.load(pkl_file)
            except PickleError:
                self._user_infos = {}
        else:
            self._user_infos = {}

    def _restore_branches(self, config):
        if os.path.exists(self._queue_pickle_file):
            try:
                pkl_file = open(self._queue_pickle_file, 'rb')
                self._branches = pickle.load(pkl_file)
            except PickleError:
                self._branches = {}

            removed_branches = [branch_name for branch_name in self._branches if
                                branch_name not in config.get_branches()]
            for branch in removed_branches:
                del self._branches[branch]
        else:
            self._branches = {}

    def add_user(self, user: User):
        if user.get_identifier() not in self._user_infos:
            self._user_infos[user.get_identifier()] = user
        else:
            raise ValueError("User with given identifier already exists")

    def get_user(self, identifier: int):
        if identifier in self._user_infos:
            return self._user_infos[identifier]
        else:
            return None

    def remove_user(self, user: User):
        if user.get_identifier() in self._user_infos:
            del self._user_infos[user.get_identifier()]
            for branch in self._branches:
                if self._branches[branch].active_user == user:
                    self._branches[branch].active_user = None
                elif user in self._branches[branch].users_queue:
                    self._branches[branch].users_queue.remove(user)
                if user in self._branches[branch].subscriptions:
                    self._branches[branch].subscriptions.remove(user)

    def get_users(self):
        return self._user_infos.copy()

    def get_identifier(self, user: User):
        for identifier in self._user_infos:
            if self._user_infos[identifier] == user:
                return identifier
        return None

    def update_or_create_user(self, identifier: int, first_name: str, last_name: str):
        last_name = " " + last_name if last_name is not None else ""
        username = html.escape(first_name + last_name, quote=True)
        user = self.get_user(identifier)
        if user is None:
            user = User(username, identifier)
            self.add_user(user)
            return True
        elif user.get_name() != username:
            user.update_name(username)
            return True
        return False

    def get_branches(self):
        return self._branches

    def dump(self):
        with open(self._users_pickle_file, 'wb') as f:
            pickle.dump(self._user_infos, f, pickle.HIGHEST_PROTOCOL)
        with open(self._queue_pickle_file, 'wb') as f:
            pickle.dump(self._branches, f, pickle.HIGHEST_PROTOCOL)
