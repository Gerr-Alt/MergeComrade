from enum import Enum

from Bot.MergeDispatcher import BranchQueue


class MergeRequestStatus(Enum):
    merge_requested = 0
    merge_started = 1
    already_in_queue = 2
    branch_not_exist = 3


class CancelRequestStatus(Enum):
    merge_cancelled = 0
    exited_from_queue = 1
    branch_not_exist = 2
    not_in_queue = 3


class DoneRequestStatus(Enum):
    merge_done = 0
    user_not_active = 1
    branch_not_exist = 2


class KickRequestStatus(Enum):
    user_kicked = 0
    user_not_in_branch = 1
    branch_not_exist = 2


class FixRequestStatus(Enum):
    fix_allowed = 0
    branch_not_exist = 1
    user_already_in_merge = 2


class SubscribeRequestStatus(Enum):
    subscription_complete = 0
    branch_not_exist = 1
    already_subscribed = 2


class UnsubscribeRequestStatus(Enum):
    unsubscription_complete = 0
    branch_not_exist = 1
    user_not_in_branch = 2


class NotifierActions(Enum):
    starts_merge = 0
    ready_to_merge = 1
    joins_queue = 2
    cancels_merge = 3
    exits_queue = 4
    done_merge = 5
    kicks_user = 6
    kicks_himself = 7
    starts_fix = 8


class Notifier:
    class ActionData:
        def __init__(self, action_user, action_branch):
            self._action_user = action_user
            self._action_branch = action_branch

        def __eq__(self, other):
            return type(self) == type(other) and \
                   self._action_user == other.get_user() and \
                   self._action_branch == other.get_branch()

        def __ne__(self, other):
            return not self == other

        def get_user(self):
            return self._action_user

        def get_branch(self):
            return self._action_branch

    class KickActionData(ActionData):
        def __init__(self, action_user, action_branch, kicked_user):
            super(Notifier.KickActionData, self).__init__(action_user, action_branch)
            self._kicked_user = kicked_user

        def __eq__(self, other):
            return super(Notifier.KickActionData, self).__eq__(other) and \
                   self._kicked_user == other.get_kicked_user()

        def get_kicked_user(self):
            return self._kicked_user

    class MergeFixActionData(ActionData):
        def __init__(self, action_user, action_branch, pushed_user):
            super(Notifier.MergeFixActionData, self).__init__(action_user, action_branch)
            self._pushed_user = pushed_user

        def __eq__(self, other):
            return super(Notifier.MergeFixActionData, self).__eq__(other) and \
                   self._pushed_user == other.get_pushed_user()

        def get_pushed_user(self):
            return self._pushed_user

    def notify(self, whom, action_type, action_data):
        raise NotImplementedError("Class %s doesn't implement notify(user, message)" % self.__class__.__name__)


class Config:
    def __init__(self, branches):
        self._branches = branches

    def get_branches(self):
        return self._branches


class Dispatcher:
    _notifier = None

    @staticmethod
    def filter_branches(branches, branch_filter):
        if branch_filter is None:
            return branches
        filtered_branches = []
        for branch in branches:
            if branch_filter.lower() in branch.lower():
                filtered_branches.append(branch)
        return filtered_branches

    def __init__(self, model, logger):
        self._model = model
        self._logger = logger

    def prepare(self):
        branches_queues = self._model.get_branches()
        for branch_name in branches_queues:
            branch_queue = branches_queues[branch_name]
            if branch_queue.active_user is None and branch_queue.users_queue:
                self._notify_users(NotifierActions.ready_to_merge,
                                   Notifier.ActionData(branch_queue.users_queue[0], branch_name))

    def set_notifier(self, notifier):
        self._notifier = notifier

    def merge(self, user_id, branch_name):
        user = self._model.get_user(user_id)
        if branch_name not in self._model.get_branches():
            self._logger.warning("Attempt to merge from user %s to non-existing branch %s", user, branch_name)
            return MergeRequestStatus.branch_not_exist

        branch = self._model.get_branches()[branch_name]
        if user in branch.users_queue or user == branch.active_user:
            self._logger.info("User %s requested merge to branch %s, but he is already in queue", user, branch_name)
            return MergeRequestStatus.already_in_queue

        if not branch.users_queue and branch.active_user is None:
            branch.active_user = user
            self._model.dump()
            self._logger.info("User %s has requested and started merge to branch %s", user, branch_name)
            self._notify_users(NotifierActions.starts_merge, Notifier.ActionData(user, branch_name))
            return MergeRequestStatus.merge_started
        else:
            branch.users_queue.append(user)
            self._model.dump()
            self._logger.info("User %s has requested merge to branch %s and was put in queue", user, branch_name)
            self._notify_users(NotifierActions.joins_queue, Notifier.ActionData(user, branch_name))
            return MergeRequestStatus.merge_requested

    def cancel(self, user_id, branch_name):
        user = self._model.get_user(user_id)
        if branch_name not in self._model.get_branches():
            self._logger.warning("User %s has requested cancel of merge to non-existing branch %s", user, branch_name)
            return CancelRequestStatus.branch_not_exist

        branch = self._model.get_branches()[branch_name]
        if branch.active_user == user:
            branch.active_user = None
            self._model.dump()
            self._logger.info("User %s has cancelled merge to branch %s", user, branch_name)
            self._notify_users(NotifierActions.cancels_merge, Notifier.ActionData(user, branch_name))
            if branch.users_queue:
                self._notify_users(NotifierActions.ready_to_merge,
                                   Notifier.ActionData(branch.users_queue[0], branch_name))
            return CancelRequestStatus.merge_cancelled
        elif user in branch.users_queue:
            first_user = branch.users_queue[0]
            branch.users_queue.remove(user)
            self._model.dump()
            self._logger.info("User %s has exited from queue to branch %s", user, branch_name)
            self._notify_users(NotifierActions.exits_queue, Notifier.ActionData(user, branch_name))

            if branch.active_user is None and first_user == user and branch.users_queue:
                self._notify_users(NotifierActions.ready_to_merge,
                                   Notifier.ActionData(branch.users_queue[0], branch_name))
            return CancelRequestStatus.exited_from_queue
        else:
            self._logger.info("User %s has requested cancel of merge to branch %s, but he is not in queue",
                              user, branch_name)
            return CancelRequestStatus.not_in_queue

    def done(self, user_id, branch_name):
        user = self._model.get_user(user_id)
        if branch_name not in self._model.get_branches():
            self._logger.warning("User %s has tried to finish merge to non-existing branch %s", user, branch_name)
            return DoneRequestStatus.branch_not_exist

        branch = self._model.get_branches()[branch_name]
        if branch.active_user != user:
            self._logger.info("User %s has tried to finish merge to branch %s, but he is not active user",
                              user, branch_name)
            return DoneRequestStatus.user_not_active

        branch.active_user = None
        self._model.dump()
        self._logger.info("User %s has finished merge to branch %s", user, branch_name)
        self._notify_users(NotifierActions.done_merge, Notifier.ActionData(user, branch_name))
        if branch.users_queue:
            self._notify_users(NotifierActions.ready_to_merge,
                               Notifier.ActionData(branch.users_queue[0], branch_name))
        return DoneRequestStatus.merge_done

    def kick(self, user_id, user_to_kick_id, branch_name):
        user = self._model.get_user(user_id)
        user_to_kick = self._model.get_user(user_to_kick_id)
        if branch_name not in self._model.get_branches():
            self._logger.warning("User %s has tried to kick user %s from non-existing branch %s",
                                 user, user_to_kick, branch_name)
            return KickRequestStatus.branch_not_exist

        branch = self._model.get_branches()[branch_name]

        next_user_will_merge = False
        if branch.active_user == user_to_kick:
            branch.active_user = None
            if len(branch.users_queue) > 0:
                next_user_will_merge = True
        elif user_to_kick in branch.users_queue:
            if branch.active_user is None and branch.users_queue[0] == user_to_kick and len(branch.users_queue) > 1:
                next_user_will_merge = True
            branch.users_queue.remove(user_to_kick)
        else:
            self._logger.warning("User %s has tried to remove user %s from branch %s, but he is not here",
                                 user, user_to_kick, branch_name)
            return KickRequestStatus.user_not_in_branch
        self._model.dump()
        action_type = NotifierActions.kicks_user if user != user_to_kick else NotifierActions.kicks_himself
        action_data = Notifier.KickActionData(user, branch_name, user_to_kick)
        self._notify_user(user_to_kick, action_type, action_data)
        self._notify_users(action_type, action_data)
        if next_user_will_merge:
            self._notify_users(NotifierActions.ready_to_merge,
                               Notifier.ActionData(branch.users_queue[0], branch_name))
        return KickRequestStatus.user_kicked

    def fix(self, user_id, branch_name):
        user = self._model.get_user(user_id)
        if branch_name not in self._model.get_branches():
            self._logger.warning("User %s has tried to merge fix in non-existing branch %s", user, branch_name)
            return FixRequestStatus.branch_not_exist
        branch = self._model.get_branches()[branch_name]
        if branch.active_user == user:
            return FixRequestStatus.user_already_in_merge

        action_data = Notifier.MergeFixActionData(user, branch_name, branch.active_user)
        if branch.active_user is not None:
            branch.users_queue.appendleft(branch.active_user)
        branch.active_user = user
        if user in branch.users_queue:
            branch.users_queue.remove(user)
        self._model.dump()
        self._notify_users(NotifierActions.starts_fix, action_data)
        return FixRequestStatus.fix_allowed

    def subscribe(self, user_id, branch_name):
        user = self._model.get_user(user_id)
        if branch_name not in self._model.get_branches():
            self._logger.warning("User %s has tried to subscribe to non-existing branch %s",
                                 user, branch_name)
            return SubscribeRequestStatus.branch_not_exist
        branch = self._model.get_branches()[branch_name]
        if user not in branch.subscriptions:
            branch.subscriptions.add(user)
            self._model.dump()
            self._logger.info("User %s has subscribed to updates in branch %s", user, branch_name)
            return SubscribeRequestStatus.subscription_complete
        else:
            self._logger.info("User %s has tried to subscribe to updates in branch %s, but he is already subscribed",
                              user, branch_name)
            return SubscribeRequestStatus.already_subscribed

    def unsubscribe(self, user_id, branch_name):
        user = self._model.get_user(user_id)
        if branch_name not in self._model.get_branches():
            self._logger.warning("User %s has tried to unsubscribe to non-existing branch %s",
                                 user, branch_name)
            return UnsubscribeRequestStatus.branch_not_exist
        branch = self._model.get_branches()[branch_name]
        if user in branch.subscriptions:
            branch.subscriptions.remove(user)
            self._model.dump()
            self._logger.info("User %s has unsubscribed from updates in branch %s", user, branch_name)
            return UnsubscribeRequestStatus.unsubscription_complete
        else:
            self._logger.info("User %s has tried to unsubscribe from updates in branch %s, but he is not subscribed",
                              user, branch_name)
            return UnsubscribeRequestStatus.user_not_in_branch

    def confirm_merge(self, user_id, branch_name):
        user = self._model.get_user(user_id)
        if branch_name not in self._model.get_branches():
            self._logger.warning("User %s has tried to confirm merge to non-existing branch %s", user, branch_name)
            return False

        branch = self._model.get_branches()[branch_name]
        if branch.active_user is None and branch.users_queue[0] == user:
            branch.active_user = branch.users_queue.popleft()
            self._model.dump()
            self._logger.info("User %s has confirmed merge to branch %s", user, branch_name)
            self._notify_users(NotifierActions.starts_merge, Notifier.ActionData(user, branch_name))
            return True
        else:
            self._logger.info("User %s tried to confirm merge to branch %s, but he can't be next", user, branch_name)
            return False

    def get_branch_queue_info(self, branch_name):
        if branch_name not in self._model.get_branches():
            return None
        else:
            branch_queue_info = BranchQueue()
            branch_queue_info.active_user = self._model.get_branches()[branch_name].active_user
            for user in self._model.get_branches()[branch_name].users_queue:
                branch_queue_info.users_queue.append(user)
            for user in self._model.get_branches()[branch_name].subscriptions:
                branch_queue_info.subscriptions.add(user)
            return branch_queue_info

    def get_all_branches(self, branch_filter=None):
        return self.filter_branches(list(self._model.get_branches().keys()), branch_filter)

    def get_branches_user_subscribed_to(self, user_id, branch_filter=None):
        user = self._model.get_user(user_id)
        result = []
        for branch in self._model.get_branches():
            if user in self._model.get_branches()[branch].subscriptions:
                result.append(branch)
        return self.filter_branches(result, branch_filter)

    def get_branches_user_not_subscribed_to(self, user_id, branch_filter=None):
        result = list(set(self.get_all_branches()) - set(self.get_branches_user_subscribed_to(user_id)))
        return self.filter_branches(result, branch_filter)

    def get_all_branches_with_user(self, user_id, branch_filter=None):
        user = self._model.get_user(user_id)
        result = []
        for branch in self._model.get_branches():
            if self._model.get_branches()[branch].active_user == user or \
                            user in self._model.get_branches()[branch].users_queue:
                result.append(branch)
        return self.filter_branches(result, branch_filter)

    def get_active_user_branches(self, user_id, branch_filter=None):
        user = self._model.get_user(user_id)
        result = []
        for branch in self._model.get_branches():
            if self._model.get_branches()[branch].active_user == user:
                result.append(branch)
        return self.filter_branches(result, branch_filter)

    def update_user(self, identifier, first_name, last_name):
        if self._model.update_or_create_user(identifier, first_name, last_name):
            self._model.dump()
            self._logger.info("User with ID %d was updated with name %s %s", identifier, first_name, last_name)

    def get_user(self, identifier):
        return self._model.get_user(identifier)

    def _notify_user(self, user, action_type, action_data):
        if self._notifier is None:
            return

        self._notifier.notify(user, action_type, action_data)

    def _notify_users(self, action_type, action_data):
        if self._notifier is None:
            return

        users_to_notify = []
        active_user = self._model.get_branches()[action_data.get_branch()].active_user
        if active_user is not None:
            users_to_notify.append(active_user)

        users_in_queue = self._model.get_branches()[action_data.get_branch()].users_queue
        for user_from_queue in users_in_queue:
            users_to_notify.append(user_from_queue)

        subscribed_users = self._model.get_branches()[action_data.get_branch()].subscriptions
        for subscribed_user in subscribed_users:
            if subscribed_user not in users_to_notify:
                users_to_notify.append(subscribed_user)

        for user_to_notify in users_to_notify:
            self._notifier.notify(user_to_notify, action_type, action_data)
