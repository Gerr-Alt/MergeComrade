import unittest
from unittest.mock import create_autospec

import logging

from Bot.MergeDispatcher import CancelRequestStatus
from Bot.MergeDispatcher import Config
from Bot.MergeDispatcher import Dispatcher
from Bot.MergeDispatcher import DoneRequestStatus
from Bot.MergeDispatcher import KickRequestStatus
from Bot.MergeDispatcher import MergeRequestStatus
from Bot.MergeDispatcher import Notifier
from Bot.MergeDispatcher import SubscribeRequestStatus
from Bot.MergeDispatcher import UnsubscribeRequestStatus
from Bot.MergeDispatcher import User
from Bot.MergeDispatcher import NotifierActions
from Bot.MergeDispatcher import BotModel
from Bot.MergeDispatcher import FixRequestStatus


class NotifierTest(unittest.TestCase):
    def test_baseClassShouldRaiseNotImplementedException(self):
        notifier = Notifier()
        with self.assertRaises(NotImplementedError):
            notifier.notify(User("Jack Daniels", 123), NotifierActions.starts_merge, None)


class UserTest(unittest.TestCase):
    def test_shouldRememberName(self):
        name = "Jack Daniels"
        user = User(name, 123)
        self.assertEqual(name, user.get_name())

    def test_shouldAllowToUpdateName(self):
        user = User("Jack Daniels", 456)
        new_name = "Jackie Daniels"
        user.update_name(new_name)
        self.assertEqual(new_name, user.get_name())


class ModelManagementTest(unittest.TestCase):
    def setUp(self):
        self._username = "Jack Daniels"
        self._identifier = 123456
        self._users_holder = BotModel(Config([]))
        self._users_holder.add_user(User(self._username, self._identifier))

    def tearDown(self):
        self._users_holder = None

    def test_shouldSaveUserWithId(self):
        identifier = 123321
        user = User("Johnny Walker", identifier)
        self._users_holder.add_user(user)
        self.assertEqual(user, self._users_holder.get_user(identifier))

    def test_shouldReturnNoneIfNoUserFound(self):
        self.assertEqual(None, self._users_holder.get_user(123321))

    def test_shouldRaiseExceptionIfUserWithIdExist(self):
        user = User("Johnny Walker", self._identifier)
        with self.assertRaises(ValueError):
            self._users_holder.add_user(user)

    def test_shouldReturnOriginalUserNotACopy(self):
        new_name = "Johnny Walker"
        self._users_holder.get_user(self._identifier).update_name(new_name)
        self.assertEqual(new_name, self._users_holder.get_user(self._identifier).get_name())

    def test_shouldReturnIdentifierOfUser(self):
        identifier = 987654
        user = User("Johnny Walker", identifier)
        self._users_holder.add_user(user)
        self.assertEqual(identifier, self._users_holder.get_identifier(user))

    def test_shouldReturnNoneIdentifierIfUserNotFound(self):
        self.assertEqual(None, self._users_holder.get_identifier(User("Chivas Regal", 343434)))

    def test_shouldAddUserWithUpdateCommandIfUserNotPersist(self):
        identifier = 123321
        first_name = "Johnny"
        second_name = "Walker"
        self._users_holder.update_or_create_user(identifier, first_name, second_name)
        self.assertEqual(first_name + " " + second_name, self._users_holder.get_user(identifier).get_name())

    def test_shouldUpdateUsernameIfUserNotExist(self):
        first_name = "Johnny"
        second_name = "Walker"
        self._users_holder.update_or_create_user(self._identifier, first_name, second_name)
        self.assertEqual(first_name + " " + second_name, self._users_holder.get_user(self._identifier).get_name())

    def test_shouldIgnoreSecondNameIfItIsNone(self):
        first_name = "Jameson"
        self._users_holder.update_or_create_user(self._identifier, first_name, None)
        self.assertEqual(first_name, self._users_holder.get_user(self._identifier).get_name())

    def test_shouldRemoveUserFromUsersDB(self):
        self._users_holder.update_or_create_user(self._identifier, self._username, None)
        self._users_holder.remove_user(self._users_holder.get_user(self._identifier))
        self.assertIsNone(self._users_holder.get_user(self._identifier))


class MergeDispatcherQueueLogicTest(unittest.TestCase):
    def setUp(self):
        self._config = Config(["default", "release"])
        self._model = BotModel(self._config)
        self._first_user_id = 123
        self._second_user_id = 456
        self._third_user_id = 789
        self._model.update_or_create_user(self._first_user_id, "Jack", "Daniels")
        self._model.update_or_create_user(self._second_user_id, "Chivas", "Regal")
        self._model.update_or_create_user(self._third_user_id, "Johnny", "Walker")
        self._merge_dispatcher = Dispatcher(self._model, logger=logging.getLogger('Tests'))

    def tearDown(self):
        self._merge_dispatcher = None

    def test_shouldReturnUserFromModel(self):
        self.assertEqual(User("Jack Daniels", self._first_user_id),
                         self._merge_dispatcher.get_user(self._first_user_id))

    def test_shouldReturnNoneIfUserNotInModel(self):
        self.assertEqual(None, self._merge_dispatcher.get_user(545))

    def test_shouldReturnMergeStartedOnMergeRequestIfQueueEmpty(self):
        result = self._merge_dispatcher.merge(self._first_user_id, self._config.get_branches()[0])
        self.assertEqual(MergeRequestStatus.merge_started, result)

    def test_shouldReturnMergeRequestedOnMergeRequestIfQueueNotEmpty(self):
        self._merge_dispatcher.merge(self._first_user_id, self._config.get_branches()[0])
        result = self._merge_dispatcher.merge(self._second_user_id, self._config.get_branches()[0])
        self.assertEqual(MergeRequestStatus.merge_requested, result)

    def test_shouldSetUserAsActiveIfQueueEmptyOnMergeRequest(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self.assertEqual(self._model.get_user(self._first_user_id),
                         self._merge_dispatcher.get_branch_queue_info(branch).active_user)

    def test_shouldReturnNoneIfNoActiveUser(self):
        self.assertEqual(None, self._merge_dispatcher.get_branch_queue_info(self._config.get_branches()[0]).active_user)

    def test_shouldRemoveUserFromActiveMerger(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._model.remove_user(self._model.get_user(self._first_user_id))
        self.assertIsNone(self._merge_dispatcher.get_branch_queue_info(branch).active_user)

    def test_shouldRemoveUserFromQueue(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._model.remove_user(self._model.get_user(self._second_user_id))
        self.assertEqual(0, len(self._merge_dispatcher.get_branch_queue_info(branch).users_queue))

    def test_shouldRemoveUserFromSubscriptions(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.subscribe(self._first_user_id, branch)
        self._merge_dispatcher.subscribe(self._second_user_id, branch)
        self._model.remove_user(self._model.get_user(self._second_user_id))
        branch_queue_info = self._merge_dispatcher.get_branch_queue_info(branch)
        self.assertEqual(1, len(branch_queue_info.subscriptions))
        self.assertNotIn(self._model.get_user(self._second_user_id), branch_queue_info.subscriptions)

    def test_shouldReturnDequeWithUsers(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        deque = self._merge_dispatcher.get_branch_queue_info(branch).users_queue
        self.assertEqual(2, len(deque))
        self.assertEqual(1, deque.count(self._model.get_user(self._second_user_id)))
        self.assertEqual(1, deque.count(self._model.get_user(self._third_user_id)))

    def test_shouldReturnNoneForBranchQueueInfoIfBranchNotExist(self):
        self.assertEqual(None, self._merge_dispatcher.get_branch_queue_info("not_so_default"))

    def test_shouldHaveDifferentQueuesForDifferentBranches(self):
        first_branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._third_user_id, first_branch)
        self._merge_dispatcher.merge(self._first_user_id, first_branch)

        second_branch = self._config.get_branches()[1]
        self._merge_dispatcher.merge(self._third_user_id, second_branch)
        self._merge_dispatcher.merge(self._second_user_id, second_branch)

        first_queue = self._merge_dispatcher.get_branch_queue_info(first_branch).users_queue
        self.assertEqual(1, len(first_queue))
        self.assertEqual(1, first_queue.count(self._model.get_user(self._first_user_id)))

        second_queue = self._merge_dispatcher.get_branch_queue_info(second_branch).users_queue
        self.assertEqual(1, len(second_queue))
        self.assertEqual(1, second_queue.count(self._model.get_user(self._second_user_id)))

    def test_shouldReturnAlreadyInQueueIfUserAlreadyInQueue(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        result = self._merge_dispatcher.merge(self._first_user_id, branch)
        self.assertEqual(MergeRequestStatus.already_in_queue, result)

    def test_shouldAllowToMergeRequestOnlyInExistingBranches(self):
        result = self._merge_dispatcher.merge(self._first_user_id, "not_default")
        self.assertEqual(MergeRequestStatus.branch_not_exist, result)

    def test_shouldAllowActiveUserToCancelMerge(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        result = self._merge_dispatcher.cancel(self._first_user_id, branch)
        self.assertEqual(CancelRequestStatus.merge_cancelled, result)

    def test_shouldAllowUserInQueueToCancelMerge(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        result = self._merge_dispatcher.cancel(self._second_user_id, branch)
        self.assertEqual(CancelRequestStatus.exited_from_queue, result)

    def test_shouldRemoveActiveUserAfterCancelIfNoUsersInQueue(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.cancel(self._first_user_id, branch)
        self.assertEqual(None, self._merge_dispatcher.get_branch_queue_info(branch).active_user)

    def test_shouldNotSelectNextUserInQueueAsActiveIfQueueNotEmpty(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.cancel(self._first_user_id, branch)
        branch_queue_info = self._merge_dispatcher.get_branch_queue_info(branch)
        self.assertEqual(None, branch_queue_info.active_user)
        self.assertEqual(1, len(branch_queue_info.users_queue))

    def test_shouldSelectNextUserInQueueAsActiveIfQueueNotEmptyAndNextUserStartMerge(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.cancel(self._first_user_id, branch)
        self._merge_dispatcher.confirm_merge(self._second_user_id, branch)
        branch_queue_info = self._merge_dispatcher.get_branch_queue_info(branch)
        self.assertEqual(self._model.get_user(self._second_user_id), branch_queue_info.active_user)
        self.assertEqual(0, len(branch_queue_info.users_queue))

    def test_shouldRemoveUserFromQueueIfHeCancelled(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.cancel(self._second_user_id, branch)
        self.assertEqual(0, len(self._merge_dispatcher.get_branch_queue_info(branch).users_queue))

    def test_shouldReturnErrorIfCancelledUserWasNotActiveOrInQueue(self):
        result = self._merge_dispatcher.cancel(self._first_user_id, self._config.get_branches()[0])
        self.assertEqual(CancelRequestStatus.not_in_queue, result)

    def test_shouldReturnErrorIfBranchFromCancelRequestNotExist(self):
        result = self._merge_dispatcher.cancel(self._first_user_id, "unused_branch")
        self.assertEqual(CancelRequestStatus.branch_not_exist, result)

    def test_shouldAllowActiveUserToDoneMerge(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        result = self._merge_dispatcher.done(self._first_user_id, branch)
        self.assertEqual(DoneRequestStatus.merge_done, result)

    def test_shouldReplaceActiveUserWithNoneIfQueueEmptyAfterDone(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.done(self._first_user_id, branch)
        self.assertEqual(None, self._merge_dispatcher.get_branch_queue_info(branch).active_user)

    def test_shouldAddNextUserFromQueueAfterDoneIfQueueNotEmpty(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.done(self._first_user_id, branch)
        branch_queue_info = self._merge_dispatcher.get_branch_queue_info(branch)
        self.assertEqual(None, branch_queue_info.active_user)
        self.assertEqual(1, len(branch_queue_info.users_queue))

    def test_shouldAddNextUserFromQueueAfterDoneIfQueueNotEmptyAndStartMergeInvoked(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.done(self._first_user_id, branch)
        self._merge_dispatcher.confirm_merge(self._second_user_id, branch)
        branch_queue_info = self._merge_dispatcher.get_branch_queue_info(branch)
        self.assertEqual(self._model.get_user(self._second_user_id), branch_queue_info.active_user)
        self.assertEqual(0, len(branch_queue_info.users_queue))

    def test_shouldReturnErrorIfUserNotActive(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        result = self._merge_dispatcher.done(self._second_user_id, branch)
        self.assertEqual(DoneRequestStatus.user_not_active, result)

    def test_shouldReturnErrorIfBranchNotExist(self):
        result = self._merge_dispatcher.done(self._first_user_id, "the_very_new_task")
        self.assertEqual(DoneRequestStatus.branch_not_exist, result)

    def test_shouldReturnFalseIfConfirmMergeCalledOnNonExistingBranch(self):
        self.assertFalse(self._merge_dispatcher.confirm_merge(self._first_user_id, "SomeBranch"))

    def test_shouldReturnFalseIfUserStartsMergeWhenHeIsNotNext(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        self._merge_dispatcher.cancel(self._first_user_id, branch)
        self.assertFalse(self._merge_dispatcher.confirm_merge(self._third_user_id, branch))

    def test_shouldReturnTrueIfUserStartsMergeWhenHeIsNext(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.cancel(self._first_user_id, branch)
        self.assertTrue(self._merge_dispatcher.confirm_merge(self._second_user_id, branch))

    def test_shouldReturnErrorIfUserKickedFromBranchWhichIsNotExist(self):
        result = self._merge_dispatcher.kick(self._first_user_id, self._second_user_id, "some_branch")
        self.assertEqual(KickRequestStatus.branch_not_exist, result)

    def test_shouldReturnErrorIfUserNotInBranch(self):
        result = self._merge_dispatcher.kick(self._first_user_id, self._second_user_id, self._config.get_branches()[0])
        self.assertEqual(KickRequestStatus.user_not_in_branch, result)

    def test_shouldKickUserInMergeFromQueue(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        result = self._merge_dispatcher.kick(self._second_user_id, self._first_user_id, branch)
        branch_queue_info = self._merge_dispatcher.get_branch_queue_info(branch)
        self.assertEqual(None, branch_queue_info.active_user)
        self.assertEqual(1, len(branch_queue_info.users_queue))
        self.assertEqual(KickRequestStatus.user_kicked, result)

    def test_shouldKickWaitingUserFromQueue(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        result = self._merge_dispatcher.kick(self._first_user_id, self._second_user_id, branch)
        branch_queue_info = self._merge_dispatcher.get_branch_queue_info(branch)
        self.assertEqual(self._first_user_id, branch_queue_info.active_user.get_identifier())
        self.assertEqual(1, len(branch_queue_info.users_queue))
        self.assertEqual(KickRequestStatus.user_kicked, result)

    def test_shouldAllowToConfirmMergeIfCurrentMergerWasKicked(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        self._merge_dispatcher.kick(self._second_user_id, self._first_user_id, branch)
        self.assertTrue(self._merge_dispatcher.confirm_merge(self._second_user_id, branch))

    def test_shouldAllowToConfirmMergeIfFirstUserInQueueWasKickedAndNoCurrentMerger(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        self._merge_dispatcher.cancel(self._first_user_id, branch)
        self._merge_dispatcher.kick(self._third_user_id, self._second_user_id, branch)
        self.assertTrue(self._merge_dispatcher.confirm_merge(self._third_user_id, branch))

    def test_shouldForbidToConfirmMergeIfFirstUserInQueueWasKickedWhileConfirming(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        self._merge_dispatcher.cancel(self._first_user_id, branch)
        self._merge_dispatcher.kick(self._third_user_id, self._second_user_id, branch)
        self.assertFalse(self._merge_dispatcher.confirm_merge(self._second_user_id, branch))

    def test_shouldNotFailWhenActiveMergerKickedAndNoUsersInQueue(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.kick(self._third_user_id, self._first_user_id, branch)

    def test_shouldNotFailWhenUserKickedFromQueueAndNoOtherUsersInQueue(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.cancel(self._first_user_id, branch)
        self._merge_dispatcher.kick(self._third_user_id, self._second_user_id, branch)

    def test_shouldAllowUserToFixBuildIfNobodyInQueue(self):
        branch = self._config.get_branches()[0]
        result = self._merge_dispatcher.fix(self._first_user_id, branch)
        self.assertEqual(FixRequestStatus.fix_allowed, result)
        branch_queue_info = self._merge_dispatcher.get_branch_queue_info(branch)
        self.assertEqual(self._model.get_user(self._first_user_id), branch_queue_info.active_user)

    def test_shouldPutCurrentUserAsFirstInQueue(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        result = self._merge_dispatcher.fix(self._third_user_id, branch)
        self.assertEqual(FixRequestStatus.fix_allowed, result)
        branch_queue_info = self._merge_dispatcher.get_branch_queue_info(branch)
        self.assertEqual(self._model.get_user(self._third_user_id), branch_queue_info.active_user)
        self.assertEqual(2, len(branch_queue_info.users_queue))
        self.assertEqual(self._model.get_user(self._first_user_id), branch_queue_info.users_queue[0])

    def test_shouldReturnBranchNotExistIfBranchNotExist(self):
        branch = "lolbranch"
        result = self._merge_dispatcher.fix(self._first_user_id, branch)
        self.assertEqual(FixRequestStatus.branch_not_exist, result)

    def test_shouldReturnErrorIfUserAlreadyInMerge(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        result = self._merge_dispatcher.fix(self._first_user_id, branch)
        self.assertEqual(FixRequestStatus.user_already_in_merge, result)

    def test_shouldRemoveUserFromQueueIfHeStartedFixFromIt(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        result = self._merge_dispatcher.fix(self._second_user_id, branch)
        self.assertEqual(FixRequestStatus.fix_allowed, result)
        branch_queue_info = self._merge_dispatcher.get_branch_queue_info(branch)
        self.assertEqual(self._model.get_user(self._second_user_id), branch_queue_info.active_user)
        self.assertEqual(1, len(branch_queue_info.users_queue))
        self.assertEqual(self._model.get_user(self._first_user_id), branch_queue_info.users_queue[0])

    def test_shouldAllowToSubscribeOnBranch(self):
        branch = self._config.get_branches()[0]
        result = self._merge_dispatcher.subscribe(self._first_user_id, branch)
        self.assertEqual(SubscribeRequestStatus.subscription_complete, result)
        branch_queue_info = self._merge_dispatcher.get_branch_queue_info(branch)
        self.assertIn(self._model.get_user(self._first_user_id), branch_queue_info.subscriptions)
        self.assertEqual(1, len(branch_queue_info.subscriptions))

    def test_shouldReturnErrorIfSubscriptionBranchDoesNotExist(self):
        result = self._merge_dispatcher.subscribe(self._first_user_id, "some_branch")
        self.assertEqual(SubscribeRequestStatus.branch_not_exist, result)

    def test_shouldReturnErrorIfUserAlreadySubscribedToBranch(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.subscribe(self._first_user_id, branch)
        result = self._merge_dispatcher.subscribe(self._first_user_id, branch)
        self.assertEqual(SubscribeRequestStatus.already_subscribed, result)

    def test_shouldAllowToUnsubscribeFromBranch(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.subscribe(self._first_user_id, branch)
        result = self._merge_dispatcher.unsubscribe(self._first_user_id, branch)
        self.assertEqual(UnsubscribeRequestStatus.unsubscription_complete, result)
        branch_queue_info = self._merge_dispatcher.get_branch_queue_info(branch)
        self.assertNotIn(self._model.get_user(self._first_user_id), branch_queue_info.subscriptions)
        self.assertEqual(0, len(branch_queue_info.subscriptions))

    def test_shouldReturnErrorIfUnsubscriptionBranchDoesNotExist(self):
        result = self._merge_dispatcher.unsubscribe(self._first_user_id, "some_branch")
        self.assertEqual(UnsubscribeRequestStatus.branch_not_exist, result)

    def test_shouldReturnErrorIfUnsubscribedUserNotInBranch(self):
        branch = self._config.get_branches()[0]
        result = self._merge_dispatcher.unsubscribe(self._first_user_id, branch)
        self.assertEqual(UnsubscribeRequestStatus.user_not_in_branch, result)


class MergeDispatcherNotifierLogicTest(unittest.TestCase):
    def setUp(self):
        self._config = Config(["default", "release"])
        self._model = BotModel(self._config)
        self._first_user_id = 123
        self._second_user_id = 456
        self._third_user_id = 789
        self._model.update_or_create_user(self._first_user_id, "Jack", "Daniels")
        self._model.update_or_create_user(self._second_user_id, "Chivas", "Regal")
        self._model.update_or_create_user(self._third_user_id, "Johnny", "Walker")
        self._merge_dispatcher = Dispatcher(self._model, logger=logging.getLogger('Tests'))
        self._notifier = create_autospec(Notifier)
        self._merge_dispatcher.set_notifier(self._notifier)

    def tearDown(self):
        self._merge_dispatcher = None

    def test_shouldNotifyWhenUserJoinsQueue(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._notifier.reset_mock()
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._notifier.notify.assert_any_call(self._model.get_user(self._first_user_id),
                                              NotifierActions.joins_queue,
                                              Notifier.ActionData(self._model.get_user(self._second_user_id), branch))

    def test_shouldNotifyWhenUserCancelMerge(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._notifier.reset_mock()
        self._merge_dispatcher.cancel(self._first_user_id, branch)
        self._notifier.notify.assert_any_call(self._model.get_user(self._second_user_id),
                                              NotifierActions.cancels_merge,
                                              Notifier.ActionData(self._model.get_user(self._first_user_id), branch))

    def test_shouldNotifyWhenUserExitsQueue(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._notifier.reset_mock()
        self._merge_dispatcher.cancel(self._second_user_id, branch)
        self._notifier.notify.assert_called_once_with(self._model.get_user(self._first_user_id),
                                                      NotifierActions.exits_queue,
                                                      Notifier.ActionData(self._model.get_user(self._second_user_id),
                                                                          branch))

    def test_shouldNotifyWhenUserExitsQueueAndNoActiveUser(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        self._merge_dispatcher.cancel(self._first_user_id, branch)
        self._notifier.reset_mock()
        self._merge_dispatcher.cancel(self._second_user_id, branch)
        self._notifier.notify.assert_any_call(self._model.get_user(self._third_user_id),
                                              NotifierActions.ready_to_merge,
                                              Notifier.ActionData(self._model.get_user(self._third_user_id), branch))

    def test_shouldNotifyOnPrepareWhenNoActiveUserBurUserInQueue(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        self._merge_dispatcher.done(self._first_user_id, branch)
        self._notifier.reset_mock()
        self._merge_dispatcher.prepare()
        self._notifier.notify.assert_any_call(self._model.get_user(self._second_user_id),
                                              NotifierActions.ready_to_merge,
                                              Notifier.ActionData(self._model.get_user(self._second_user_id), branch))

    def test_shouldNotifyWhenNextUserFromQueueReadyToMergeAfterCancel(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        self._notifier.reset_mock()
        self._merge_dispatcher.cancel(self._first_user_id, branch)
        self._notifier.notify.assert_any_call(self._model.get_user(self._second_user_id),
                                              NotifierActions.ready_to_merge,
                                              Notifier.ActionData(self._model.get_user(self._second_user_id), branch))

    def test_shouldNotifyWhenUserDoneMerge(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._notifier.reset_mock()
        self._merge_dispatcher.done(self._first_user_id, branch)
        self._notifier.notify.assert_any_call(self._model.get_user(self._second_user_id),
                                              NotifierActions.done_merge,
                                              Notifier.ActionData(self._model.get_user(self._first_user_id), branch))

    def test_shouldNotifyWhenNextUserFromQueueReadyToMergeAfterDone(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        self._notifier.reset_mock()
        self._merge_dispatcher.done(self._first_user_id, branch)
        self._notifier.notify.assert_any_call(self._model.get_user(self._second_user_id),
                                              NotifierActions.ready_to_merge,
                                              Notifier.ActionData(self._model.get_user(self._second_user_id), branch))

    def test_shouldNotifyIfUserStartsMergeWhenHeIsNext(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        self._merge_dispatcher.cancel(self._first_user_id, branch)
        self._merge_dispatcher.confirm_merge(self._second_user_id, branch)
        self._notifier.notify.assert_any_call(self._model.get_user(self._third_user_id),
                                              NotifierActions.starts_merge,
                                              Notifier.ActionData(self._model.get_user(self._second_user_id), branch))

    def test_shouldNotifyUsersWhenUserKicksAnotherUser(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        self._merge_dispatcher.kick(self._first_user_id, self._second_user_id, branch)
        action_data = Notifier.KickActionData(self._model.get_user(self._first_user_id), branch,
                                              self._model.get_user(self._second_user_id))

        self._notifier.notify.assert_any_call(self._model.get_user(self._second_user_id), NotifierActions.kicks_user,
                                              action_data)
        self._notifier.notify.assert_any_call(self._model.get_user(self._third_user_id), NotifierActions.kicks_user,
                                              action_data)

    def test_shouldNotifyUsersWhenUserKicksHimself(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.kick(self._first_user_id, self._first_user_id, branch)
        action_data = Notifier.KickActionData(self._model.get_user(self._first_user_id), branch,
                                              self._model.get_user(self._first_user_id))

        self._notifier.notify.assert_any_call(self._model.get_user(self._first_user_id), NotifierActions.kicks_himself,
                                              action_data)
        self._notifier.notify.assert_any_call(self._model.get_user(self._second_user_id), NotifierActions.kicks_himself,
                                              action_data)

    def test_shouldNotifyWhenNextUserFromQueueReadyToMergeAfterKick(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        self._notifier.reset_mock()
        self._merge_dispatcher.kick(self._second_user_id, self._first_user_id, branch)
        self._notifier.notify.assert_any_call(self._model.get_user(self._second_user_id),
                                              NotifierActions.ready_to_merge,
                                              Notifier.ActionData(self._model.get_user(self._second_user_id), branch))

    def test_shouldNotifyWhenNextUserFromQueueReadyToMergeAfterKickOfFirstInQueueAndNoActiveMerger(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        self._merge_dispatcher.cancel(self._first_user_id, branch)
        self._notifier.reset_mock()
        self._merge_dispatcher.kick(self._third_user_id, self._second_user_id, branch)
        self._notifier.notify.assert_any_call(self._model.get_user(self._third_user_id),
                                              NotifierActions.ready_to_merge,
                                              Notifier.ActionData(self._model.get_user(self._third_user_id), branch))

    def test_shouldNotifyActiveUserWhenHeIsPutBackToQueue(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._notifier.reset_mock()
        self._merge_dispatcher.fix(self._second_user_id, branch)
        self._notifier.notify.assert_any_call(self._model.get_user(self._first_user_id),
                                              NotifierActions.starts_fix,
                                              Notifier.MergeFixActionData(self._model.get_user(self._second_user_id),
                                                                          branch,
                                                                          self._model.get_user(self._first_user_id)))

    def test_shouldNotifyUsersWhenSomeoneStartsFix(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._first_user_id, branch)
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._notifier.reset_mock()
        self._merge_dispatcher.fix(self._third_user_id, branch)
        self._notifier.notify.assert_any_call(self._model.get_user(self._first_user_id),
                                              NotifierActions.starts_fix,
                                              Notifier.MergeFixActionData(self._model.get_user(self._third_user_id),
                                                                          branch,
                                                                          self._model.get_user(self._first_user_id)))

    def test_shouldNotifyUserWhenHeIsSubscribedToQueue(self):
        branch = self._config.get_branches()[0]
        self._merge_dispatcher.subscribe(self._first_user_id, branch)
        self._notifier.reset_mock()
        self._merge_dispatcher.merge(self._second_user_id, branch)
        self._merge_dispatcher.merge(self._third_user_id, branch)
        self._notifier.notify.assert_any_call(self._model.get_user(self._first_user_id),
                                              NotifierActions.starts_merge,
                                              Notifier.ActionData(self._model.get_user(self._second_user_id), branch))
        self._notifier.notify.assert_any_call(self._model.get_user(self._first_user_id),
                                              NotifierActions.joins_queue,
                                              Notifier.ActionData(self._model.get_user(self._third_user_id), branch))


class MergeDispatcherUserManagementTest(unittest.TestCase):
    def setUp(self):
        self._model = create_autospec(BotModel)
        self._merge_dispatcher = Dispatcher(self._model, logger=logging.getLogger('Tests'))

    def tearDown(self):
        self._merge_dispatcher = None
        self._model = None

    def test_shouldDelegateUserCreationToModel(self):
        identifier = 123
        first_name = "Jack"
        second_name = "Daniels"
        self._merge_dispatcher.update_user(identifier, first_name, second_name)
        self._model.update_or_create_user.assert_any_call(identifier, first_name, second_name)


class MergeDispatcherBranchInformationTest(unittest.TestCase):
    def setUp(self):
        self._config = Config(["default", "release"])
        model = BotModel(self._config)
        self._first_user_id = 123
        self._second_user_id = 456
        model.update_or_create_user(self._first_user_id, "Jack", "Daniels")
        model.update_or_create_user(self._second_user_id, "Johnny", "Walker")
        self._merge_dispatcher = Dispatcher(model, logger=logging.getLogger('Tests'))

    def tearDown(self):
        self._merge_dispatcher = None

    def test_shouldReturnCollectionOfBranchesUserCanCancel(self):
        self._merge_dispatcher.merge(self._second_user_id, self._config.get_branches()[0])
        all_branches = self._config.get_branches()
        for branch in all_branches:
            self._merge_dispatcher.merge(self._first_user_id, branch)

        user_branches = set(self._merge_dispatcher.get_all_branches_with_user(self._first_user_id))
        self.assertSetEqual(set(all_branches), user_branches)

    def test_shouldReturnCollectionOfBranchesUserCanDone(self):

        exclude_branch = self._config.get_branches()[0]
        self._merge_dispatcher.merge(self._second_user_id, exclude_branch)
        all_branches = self._config.get_branches()
        for branch in all_branches:
            self._merge_dispatcher.merge(self._first_user_id, branch)

        user_branches = set(self._merge_dispatcher.get_active_user_branches(self._first_user_id))
        self.assertSetEqual(set(all_branches).difference({exclude_branch}), user_branches)

    def test_shouldReturnEmptyCollectionIfUserNotInterestedInAnyBranches(self):
        user_branches = self._merge_dispatcher.get_all_branches_with_user(self._first_user_id)
        self.assertSetEqual(set(), set(user_branches))

    def test_shouldReturnAllBranches(self):
        self.assertSetEqual(set(self._config.get_branches()), set(self._merge_dispatcher.get_all_branches()))

    def test_shouldSupportOptionalFilterInGetAllBranches(self):
        self.assertSetEqual({"default"}, set(self._merge_dispatcher.get_all_branches(branch_filter="def")))

    def test_shouldSupportOptionalFilterInGetBranchesWithUser(self):
        all_branches = self._config.get_branches()
        for branch in all_branches:
            self._merge_dispatcher.merge(self._first_user_id, branch)

        user_branches = set(self._merge_dispatcher.get_all_branches_with_user(self._first_user_id, branch_filter="def"))
        self.assertSetEqual({"default"}, user_branches)

    def test_shouldSupportOptionalFilterInGetActiveBranches(self):
        all_branches = self._config.get_branches()
        for branch in all_branches:
            self._merge_dispatcher.merge(self._first_user_id, branch)

        user_branches = set(self._merge_dispatcher.get_active_user_branches(self._first_user_id, branch_filter="def"))
        self.assertSetEqual({"default"}, user_branches)

    def test_shouldReturnBranchesUserSubscribedTo(self):
        self._merge_dispatcher.subscribe(self._first_user_id, "default")

        user_branches = set(self._merge_dispatcher.get_branches_user_subscribed_to(self._first_user_id))
        self.assertSetEqual({"default"}, user_branches)

    def test_shouldReturnBranchesUserNotSubscribedTo(self):
        self._merge_dispatcher.subscribe(self._first_user_id, "default")

        user_branches = set(self._merge_dispatcher.get_branches_user_not_subscribed_to(self._first_user_id))
        self.assertSetEqual({"release"}, user_branches)
