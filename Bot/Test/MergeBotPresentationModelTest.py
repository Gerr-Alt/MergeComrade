import unittest
from collections import deque
from unittest.mock import create_autospec

from Bot.MergeDispatcher import BotPresentationModel
from Bot.MergeDispatcher import BranchQueue
from Bot.MergeDispatcher import CancelRequestStatus
from Bot.MergeDispatcher import Dispatcher
from Bot.MergeDispatcher import DoneRequestStatus
from Bot.MergeDispatcher import FixRequestStatus
from Bot.MergeDispatcher import KickRequestStatus
from Bot.MergeDispatcher import MergeRequestStatus
from Bot.MergeDispatcher import MessageSender
from Bot.MergeDispatcher import Messages
from Bot.MergeDispatcher import Notifier
from Bot.MergeDispatcher import NotifierActions
from Bot.MergeDispatcher import States
from Bot.MergeDispatcher import SubscribeRequestStatus
from Bot.MergeDispatcher import UnsubscribeRequestStatus
from Bot.MergeDispatcher import User
from Bot.MergeDispatcher import BotModel


class MessageSenderTests(unittest.TestCase):
    def test_shouldThrowNotImplementedExceptionFromBaseClassForSend(self):
        message_sender = MessageSender()
        with self.assertRaises(NotImplementedError):
            message_sender.send(123, "message")

    def test_shouldThrowNotImplementedExceptionFromBaseClassForBranchSelector(self):
        message_sender = MessageSender()
        with self.assertRaises(NotImplementedError):
            message_sender.send_branch_selector(123, States.merge, "message", ["default"])

    def test_shouldThrowNotImplementedExceptionFromBaseClassForMergeConfirmation(self):
        message_sender = MessageSender()
        with self.assertRaises(NotImplementedError):
            message_sender.request_merge_confirmation(123, "message", "default")


class BotPresentationModelMergeLogicTest(unittest.TestCase):
    def setUp(self):
        self._branch = "default"
        self._merge_dispatcher = create_autospec(Dispatcher)
        self._merge_dispatcher.get_all_branches.return_value = [self._branch]
        self._message_sender = create_autospec(MessageSender)
        self._users_holder = create_autospec(BotModel)
        self._presentation_model = BotPresentationModel(self._merge_dispatcher, self._message_sender)
        self._identifier = 123321

    def tearDown(self):
        self._presentation_model = None

    def test_shouldCheckCollectionWithBranchesPossibleToMerge(self):
        branch_filter = "filter"
        self._presentation_model.request_merge(self._identifier, branch_filter=branch_filter)
        self._merge_dispatcher.get_all_branches.assert_called_once_with(branch_filter)

    def test_shouldShowMessageIfNoBranchesAvailable(self):
        self._merge_dispatcher.get_all_branches.return_value = []
        self._presentation_model.request_merge(self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.MERGE_NO_BRANCHES_AVAILABLE)

    def test_shouldCallMessageSenderWithBranchSelectorIfMultipleBranchesAvailable(self):
        branches = ["default", "release", "something_else"]
        self._merge_dispatcher.get_all_branches.return_value = branches
        self._presentation_model.request_merge(self._identifier)
        self._message_sender.send_branch_selector.assert_called_once_with(self._identifier,
                                                                          States.merge,
                                                                          Messages.MERGE_SELECT_BRANCH_MESSAGE,
                                                                          branches)

    def test_shouldStartMergeForSelectedBranch(self):
        self._presentation_model.request_merge(self._identifier, self._branch)
        self._merge_dispatcher.merge.assert_called_once_with(self._identifier, self._branch)

    def test_shouldNotCallMessageSenderIfMergeRequestWasSuccessfulAndMergeWasStarted(self):
        self._merge_dispatcher.merge.return_value = MergeRequestStatus.merge_started
        self._presentation_model.request_merge(self._identifier, self._branch)
        self._message_sender.send.assert_not_called()

    def test_shouldCallMessageSenderIfMergeRequestWasSuccessfulAndUserPlacedInQueue(self):
        active_user = User("Johnny Walker", 8888)
        user_in_queue = User("Chivas Regal", 9999)
        branch_queue_info = BranchQueue()
        branch_queue_info.active_user = active_user
        branch_queue_info.users_queue = deque([user_in_queue])
        self._merge_dispatcher.get_branch_queue_info.return_value = branch_queue_info
        self._merge_dispatcher.merge.return_value = MergeRequestStatus.merge_requested
        self._presentation_model.request_merge(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.MERGE_ADDED_TO_QUEUE_MESSAGE.format("2nd",
                                                                                                       self._branch))

    def test_shouldCallMessageSenderIfMergeRequestWasUnsuccessfulBecauseUserAlreadyInQueue(self):
        self._merge_dispatcher.merge.return_value = MergeRequestStatus.already_in_queue
        self._presentation_model.request_merge(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.MERGE_ALREADY_IN_QUEUE_MESSAGE.format(self._branch))

    def test_shouldCallMessageSenderIfMergeRequestWasUnsuccessfulBecauseOfNonExistingBranch(self):
        self._merge_dispatcher.merge.return_value = MergeRequestStatus.branch_not_exist
        self._presentation_model.request_merge(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.MERGE_BRANCH_NOT_EXIST_MESSAGE.format(self._branch))

    def test_shouldHaveConfirmMergeMethodWhichCallsStartMergeMethodOfDispatcher(self):
        self._presentation_model.confirm_merge(self._identifier, self._branch)
        self._merge_dispatcher.confirm_merge.assert_called_once_with(self._identifier, self._branch)

    def test_shouldPrintErrorIfConfirmMergeReturnsFalse(self):
        self._merge_dispatcher.confirm_merge.return_value = False
        self._presentation_model.confirm_merge(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.CONFIRM_MERGE_FAILED_MESSAGE.format(self._branch))


class BotPresentationModelCancelLogicTest(unittest.TestCase):
    def setUp(self):
        self._branch = "default"
        self._merge_dispatcher = create_autospec(Dispatcher)
        self._merge_dispatcher.get_all_branches_with_user.return_value = [self._branch]
        self._message_sender = create_autospec(MessageSender)
        self._users_holder = create_autospec(BotModel)
        self._presentation_model = BotPresentationModel(self._merge_dispatcher, self._message_sender)

        self._identifier = 123456

    def tearDown(self):
        self._presentation_model = None

    def test_shouldCheckCollectionWithBranchesPossibleToCancel(self):
        branch_filter = "filter"
        self._presentation_model.request_cancel(self._identifier, branch_filter=branch_filter)
        self._merge_dispatcher.get_all_branches_with_user.assert_called_once_with(self._identifier, branch_filter)

    def test_shouldShowMessageIfNoBranchesAvailable(self):
        self._merge_dispatcher.get_all_branches_with_user.return_value = []
        self._presentation_model.request_cancel(self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.CANCEL_NO_BRANCHES_AVAILABLE)

    def test_shouldCallMessageSenderWithBranchSelectorIfMultipleBranchesAvailable(self):
        branches = ["default", "release", "something_else"]
        self._merge_dispatcher.get_all_branches_with_user.return_value = branches
        self._presentation_model.request_cancel(self._identifier)
        self._message_sender.send_branch_selector.assert_called_once_with(self._identifier,
                                                                          States.cancel,
                                                                          Messages.CANCEL_SELECT_BRANCH_MESSAGE,
                                                                          branches)

    def test_shouldCancelMergeInSelectedBranch(self):
        self._presentation_model.request_cancel(self._identifier, self._branch)
        self._merge_dispatcher.cancel.assert_called_once_with(self._identifier, self._branch)

    def test_shouldCallMessageSenderIfCancelWasCalledAndMergeWasAborted(self):
        self._merge_dispatcher.cancel.return_value = CancelRequestStatus.merge_cancelled
        self._presentation_model.request_cancel(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.CANCEL_MERGE_CANCELLED_MESSAGE.format(self._branch))

    def test_shouldCallMessageSenderIfCancelWasCalledUserExitedFromQueue(self):
        self._merge_dispatcher.cancel.return_value = CancelRequestStatus.exited_from_queue
        self._presentation_model.request_cancel(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.CANCEL_EXITED_FROM_QUEUE_MESSAGE.format(
                                                              self._branch))

    def test_shouldCallMessageSenderIfCancelWasCalledWithIncorrectBranch(self):
        self._merge_dispatcher.cancel.return_value = CancelRequestStatus.branch_not_exist
        self._presentation_model.request_cancel(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.CANCEL_BRANCH_NOT_EXIST_MESSAGE.format(self._branch))

    def test_shouldCallMessageSenderIfCancelWasCalledWhenUserNotInQueue(self):
        self._merge_dispatcher.cancel.return_value = CancelRequestStatus.not_in_queue
        self._presentation_model.request_cancel(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.CANCEL_NOT_IN_QUEUE_MESSAGE.format(self._branch))


class BotPresentationModelDoneLogicTest(unittest.TestCase):
    def setUp(self):
        self._branch = "default"
        self._merge_dispatcher = create_autospec(Dispatcher)
        self._merge_dispatcher.get_active_user_branches.return_value = [self._branch]
        self._message_sender = create_autospec(MessageSender)
        self._users_holder = create_autospec(BotModel)
        self._presentation_model = BotPresentationModel(self._merge_dispatcher, self._message_sender)

        self._identifier = 123456

    def tearDown(self):
        self._presentation_model = None

    def test_shouldAskCollectionWithBranchesPossibleToDone(self):
        branch_filter = "filter"
        self._presentation_model.request_done(self._identifier, branch_filter=branch_filter)
        self._merge_dispatcher.get_active_user_branches.assert_called_once_with(self._identifier, branch_filter)

    def test_shouldShowMessageIfNoBranchesAvailable(self):
        self._merge_dispatcher.get_active_user_branches.return_value = []
        self._presentation_model.request_done(self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.DONE_NO_BRANCHES_AVAILABLE)

    def test_shouldCallMessageSenderWithBranchSelectorIfMultipleBranchesAvailable(self):
        branches = ["default", "release", "something_else"]
        self._merge_dispatcher.get_active_user_branches.return_value = branches
        self._presentation_model.request_done(self._identifier)
        self._message_sender.send_branch_selector.assert_called_once_with(self._identifier,
                                                                          States.done,
                                                                          Messages.DONE_SELECT_BRANCH_MESSAGE,
                                                                          branches)

    def test_shouldDoneMergeInSelectedBranch(self):
        self._presentation_model.request_done(self._identifier, self._branch)
        self._merge_dispatcher.done.assert_called_once_with(self._identifier, self._branch)

    def test_shouldCallMessageSenderIfDoneWasCalledSuccessfully(self):
        self._merge_dispatcher.done.return_value = DoneRequestStatus.merge_done
        self._presentation_model.request_done(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.DONE_MERGE_DONE_MESSAGE.format(self._branch))

    def test_shouldCallMessageSenderIfDoneWasCalledButUserAreNotActiveMerger(self):
        self._merge_dispatcher.done.return_value = DoneRequestStatus.user_not_active
        self._presentation_model.request_done(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.DONE_NOT_YOUR_TURN_MESSAGE.format(self._branch))

    def test_shouldCallMessageSenderIfDoneWasCalledButBranchAreNotExist(self):
        self._merge_dispatcher.done.return_value = DoneRequestStatus.branch_not_exist
        self._presentation_model.request_done(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.DONE_BRANCH_NOT_EXIST_MESSAGE.format(self._branch))


class BotPresentationModelQueueLogicTest(unittest.TestCase):
    def setUp(self):
        self._branch = "default"
        self._merge_dispatcher = create_autospec(Dispatcher)
        self._merge_dispatcher.get_all_branches.return_value = [self._branch]
        self._message_sender = create_autospec(MessageSender)
        self._users_holder = create_autospec(BotModel)
        self._presentation_model = BotPresentationModel(self._merge_dispatcher, self._message_sender)
        self._identifier = 123456
        self._user = User("Jack Daniels", self._identifier)

    def tearDown(self):
        self._presentation_model = None

    def test_shouldAskCollectionWithBranchesForQueueInformation(self):
        branch_filter = "filter"
        self._presentation_model.request_queue_info(self._identifier, branch_filter=branch_filter)
        self._merge_dispatcher.get_all_branches.assert_called_once_with(branch_filter)

    def test_shouldShowMessageIfNoBranchesAvailable(self):
        self._merge_dispatcher.get_all_branches.return_value = []
        self._presentation_model.request_queue_info(self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.QUEUE_NO_BRANCHES_AVAILABLE)

    def test_shouldCallMessageSenderWithBranchSelectorIfMultipleBranchesAvailable(self):
        branches = ["default", "release", "something_else"]
        self._merge_dispatcher.get_all_branches.return_value = branches
        self._presentation_model.request_queue_info(self._identifier)
        self._message_sender.send_branch_selector.assert_called_once_with(self._identifier,
                                                                          States.queue,
                                                                          Messages.QUEUE_SELECT_BRANCH_MESSAGE,
                                                                          branches)

    def test_shouldGetActiveUserAndQueueFromDispatcher(self):
        self._presentation_model.request_queue_info(self._identifier, self._branch)
        self._merge_dispatcher.get_branch_queue_info.assert_called_once_with(self._branch)

    def test_shouldCallMessageSenderIfNoActiveUserAndQueueIsEmpty(self):
        self._merge_dispatcher.get_branch_queue_info.return_value = BranchQueue()
        self._presentation_model.request_queue_info(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.QUEUE_EMPTY_INFO_MESSAGE.format(self._branch))

    def test_shouldCallMessageSenderIfNoBranchInfo(self):
        self._merge_dispatcher.get_branch_queue_info.return_value = None
        self._presentation_model.request_queue_info(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.QUEUE_BRANCH_NOT_EXIST_MESSAGE.format(self._branch))

    def test_shouldCallMessageSenderIfOnlyActiveUserInQueue(self):
        active_user = User("Johnny Walker", 90909)
        branch_queue_info = BranchQueue()
        branch_queue_info.active_user = active_user
        self._merge_dispatcher.get_branch_queue_info.return_value = branch_queue_info
        self._presentation_model.request_queue_info(self._identifier, self._branch)
        users_list = Messages.QUEUE_INFO_USER_IN_MERGE.format(active_user.get_name())
        message = Messages.QUEUE_INFO_MESSAGE.format(self._branch, users_list)
        self._message_sender.send.assert_called_once_with(self._identifier, message)

    def test_shouldCallMessageSenderIfOnlyActiveUserInQueueAndHeIsCurrentUserFromRequest(self):
        branch_queue_info = BranchQueue()
        branch_queue_info.active_user = self._user
        self._merge_dispatcher.get_branch_queue_info.return_value = branch_queue_info
        self._presentation_model.request_queue_info(self._identifier, self._branch)
        users_list = Messages.QUEUE_INFO_CURRENT_USER_IN_MERGE.format(self._user.get_name())
        message = Messages.QUEUE_INFO_MESSAGE.format(self._branch, users_list)
        self._message_sender.send.assert_called_once_with(self._identifier, message)

    def test_shouldCallMessageSenderIfUsersInQueue(self):
        active_user = User("Johnny Walker", 8888)
        user_in_queue = User("Chivas Regal", 9999)
        branch_queue_info = BranchQueue()
        branch_queue_info.active_user = active_user
        branch_queue_info.users_queue = deque([user_in_queue])
        self._merge_dispatcher.get_branch_queue_info.return_value = branch_queue_info
        self._presentation_model.request_queue_info(self._identifier, self._branch)
        users_list = Messages.QUEUE_INFO_USER_IN_MERGE.format(active_user.get_name())
        users_list += Messages.QUEUE_INFO_USER_IN_QUEUE.format(user_in_queue.get_name())
        message = Messages.QUEUE_INFO_MESSAGE.format(self._branch, users_list)
        self._message_sender.send.assert_called_once_with(self._identifier, message)

    def test_shouldCallMessageSenderIfUserInQueueCurrent(self):
        active_user = User("Johnny Walker", 45454)
        branch_queue_info = BranchQueue()
        branch_queue_info.active_user = active_user
        branch_queue_info.users_queue = deque([self._user])
        self._merge_dispatcher.get_branch_queue_info.return_value = branch_queue_info
        self._presentation_model.request_queue_info(self._identifier, self._branch)
        users_list = Messages.QUEUE_INFO_USER_IN_MERGE.format(active_user.get_name())
        users_list += Messages.QUEUE_INFO_CURRENT_USER_IN_QUEUE.format(self._user.get_name())
        message = Messages.QUEUE_INFO_MESSAGE.format(self._branch, users_list)
        self._message_sender.send.assert_called_once_with(self._identifier, message)

    def test_shouldWorkIfNoActiveUserButUsersInQueue(self):
        branch_queue_info = BranchQueue()
        branch_queue_info.active_user = None
        branch_queue_info.users_queue = deque([self._user])
        self._merge_dispatcher.get_branch_queue_info.return_value = branch_queue_info
        self._presentation_model.request_queue_info(self._identifier, self._branch)
        users_list = Messages.QUEUE_INFO_CURRENT_USER_IN_QUEUE.format(self._user.get_name())
        message = Messages.QUEUE_INFO_MESSAGE.format(self._branch, users_list)
        self._message_sender.send.assert_called_once_with(self._identifier, message)


class BotPresentationModelKickTest(unittest.TestCase):
    def setUp(self):
        self._branch = "default"
        self._merge_dispatcher = create_autospec(Dispatcher)
        self._merge_dispatcher.get_all_branches.return_value = [self._branch]
        self._message_sender = create_autospec(MessageSender)
        self._users_holder = create_autospec(BotModel)
        self._presentation_model = BotPresentationModel(self._merge_dispatcher, self._message_sender)
        self._identifier = 123456
        self._user = User("Jack Daniels", self._identifier)

    def tearDown(self):
        self._presentation_model = None

    def test_shouldAskCollectionWithBranchesForKickCommand(self):
        branch_filter = "filter"
        self._presentation_model.request_kick(self._identifier, branch_filter=branch_filter)
        self._merge_dispatcher.get_all_branches.assert_called_once_with(branch_filter)

    def test_shouldShowMessageIfNoBranchesAvailable(self):
        self._merge_dispatcher.get_all_branches.return_value = []
        self._presentation_model.request_kick(self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.KICK_NO_BRANCHES_AVAILABLE)

    def test_shouldCallMessageSenderWithBranchSelectorIfMultipleBranchesAvailable(self):
        branches = ["default", "release", "something_else"]
        self._merge_dispatcher.get_all_branches.return_value = branches
        self._presentation_model.request_kick(self._identifier)
        self._message_sender.send_branch_selector.assert_called_once_with(self._identifier,
                                                                          States.kick,
                                                                          Messages.KICK_SELECT_BRANCH_MESSAGE,
                                                                          branches)

    def test_shouldSendMessageIfNoUsersInBranch(self):
        branch_queue_info = BranchQueue()
        branch_queue_info.active_user = None
        branch_queue_info.users_queue = deque()
        self._merge_dispatcher.get_branch_queue_info.return_value = branch_queue_info
        self._presentation_model.request_kick(self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.KICK_NO_USERS_TO_KILL)

    def test_shouldSendMessageIfBranchIsNone(self):
        self._merge_dispatcher.get_branch_queue_info.return_value = None
        self._presentation_model.request_kick(self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.KICK_BRANCH_NOT_EXIST.format(self._branch))

    def test_shouldSendMessageWithUsersListIfUsersInBranch(self):
        active_user = User("Johnny Walker", 8888)
        user_in_queue = User("Chivas Regal", 9999)
        branch_queue_info = BranchQueue()
        branch_queue_info.active_user = active_user
        branch_queue_info.users_queue = deque([user_in_queue, self._user])
        self._merge_dispatcher.get_branch_queue_info.return_value = branch_queue_info
        self._presentation_model.request_kick(self._identifier)
        self._message_sender.send_user_selector.assert_called_once_with(self._identifier,
                                                                        States.kick,
                                                                        Messages.KICK_SELECT_USER,
                                                                        [active_user, user_in_queue, self._user],
                                                                        MessageSender.Payload(branch=self._branch))

    def test_shouldSendMessageIfUserWasKicked(self):
        user_id = 9999
        active_user = User("Chivas Regal", user_id)
        branch_queue_info = BranchQueue()
        branch_queue_info.active_user = active_user
        self._merge_dispatcher.get_branch_queue_info.return_value = branch_queue_info
        self._merge_dispatcher.kick.return_value = KickRequestStatus.user_kicked
        self._presentation_model.request_kick(self._identifier, self._branch, user_id)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.KICK_USER_WAS_KICKED)

    def test_shouldSendMessageIfBranchNotFoundWhileKickingUser(self):
        self._merge_dispatcher.kick.return_value = KickRequestStatus.branch_not_exist
        self._presentation_model.request_kick(self._identifier, self._branch, self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.KICK_BRANCH_NOT_EXIST.format(self._branch))

    def test_shouldSendMessageIfUserWasNotFound(self):
        self._merge_dispatcher.kick.return_value = KickRequestStatus.user_not_in_branch
        self._merge_dispatcher.get_user.return_value = self._user
        self._presentation_model.request_kick(self._identifier, self._branch, self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.KICK_USER_NOT_IN_BRANCH.format(self._user.get_name(),
                                                                                                  self._branch))

    def test_shouldSendMessageIfUserNotInDatabase(self):
        self._merge_dispatcher.kick.return_value = KickRequestStatus.user_not_in_branch
        self._merge_dispatcher.get_user.return_value = None
        self._presentation_model.request_kick(self._identifier, self._branch, self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier, Messages.KICK_USER_NOT_EXIST)

    def test_shouldNotSendMessageIfUserWasKickedAndKickedUserSameWithRequesterID(self):
        branch_queue_info = BranchQueue()
        branch_queue_info.active_user = self._user
        self._merge_dispatcher.get_branch_queue_info.return_value = branch_queue_info
        self._merge_dispatcher.kick.return_value = KickRequestStatus.user_kicked
        self._presentation_model.request_kick(self._identifier, self._branch, self._identifier)
        self._message_sender.send.assert_not_called()


class BotPresentationModelFixTest(unittest.TestCase):
    def setUp(self):
        self._branch = "default"
        self._merge_dispatcher = create_autospec(Dispatcher)
        self._merge_dispatcher.get_all_branches.return_value = [self._branch]
        self._message_sender = create_autospec(MessageSender)
        self._users_holder = create_autospec(BotModel)
        self._presentation_model = BotPresentationModel(self._merge_dispatcher, self._message_sender)

        self._identifier = 123456

    def tearDown(self):
        self._presentation_model = None

    def test_shouldAskCollectionWithBranchesPossibleToFix(self):
        branch_filter = "filter"
        self._presentation_model.request_fix(self._identifier, branch_filter=branch_filter)
        self._merge_dispatcher.get_all_branches.assert_called_once_with(branch_filter)

    def test_shouldShowMessageIfNoBranchesAvailable(self):
        self._merge_dispatcher.get_all_branches.return_value = []
        self._presentation_model.request_fix(self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.FIX_NO_BRANCHES_AVAILABLE)

    def test_shouldCallMessageSenderWithBranchSelectorIfMultipleBranchesAvailable(self):
        branches = ["default", "release", "something_else"]
        self._merge_dispatcher.get_all_branches.return_value = branches
        self._presentation_model.request_fix(self._identifier)
        self._message_sender.send_branch_selector.assert_called_once_with(self._identifier,
                                                                          States.fix,
                                                                          Messages.FIX_SELECT_BRANCH_MESSAGE,
                                                                          branches)

    def test_shouldFixMergeInSelectedBranch(self):
        self._presentation_model.request_fix(self._identifier, self._branch)
        self._merge_dispatcher.fix.assert_called_once_with(self._identifier, self._branch)

    def test_shouldCallMessageSenderIfMergeFixWasAllowed(self):
        self._merge_dispatcher.fix.return_value = FixRequestStatus.fix_allowed
        self._presentation_model.request_fix(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.FIX_MERGE_ALLOWED_MESSAGE.format(self._branch))

    def test_shouldCallMessageSenderIfUserAlreadyInMerge(self):
        self._merge_dispatcher.fix.return_value = FixRequestStatus.user_already_in_merge
        self._presentation_model.request_fix(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.FIX_ALREADY_IN_MERGE_MESSAGE.format(self._branch))

    def test_shouldCallMessageSenderIfFixWasCalledButBranchAreNotExist(self):
        self._merge_dispatcher.fix.return_value = FixRequestStatus.branch_not_exist
        self._presentation_model.request_fix(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.FIX_BRANCH_NOT_EXIST_MESSAGE.format(self._branch))


class BotPresentationModelSubscribeTest(unittest.TestCase):
    def setUp(self):
        self._branch = "default"
        self._merge_dispatcher = create_autospec(Dispatcher)
        self._merge_dispatcher.get_branches_user_not_subscribed_to.return_value = [self._branch]
        self._message_sender = create_autospec(MessageSender)
        self._users_holder = create_autospec(BotModel)
        self._presentation_model = BotPresentationModel(self._merge_dispatcher, self._message_sender)

        self._identifier = 123456

    def tearDown(self):
        self._presentation_model = None

    def test_shouldAskCollectionWithBranchesPossibleToSubscribe(self):
        branch_filter = "filter"
        self._presentation_model.request_subscribe(self._identifier, branch_filter=branch_filter)
        self._merge_dispatcher.get_branches_user_not_subscribed_to.assert_called_once_with(self._identifier,
                                                                                           branch_filter)

    def test_shouldShowMessageIfNoBranchesAvailable(self):
        self._merge_dispatcher.get_all_branches.return_value = []
        self._merge_dispatcher.get_branches_user_not_subscribed_to.return_value = []
        self._presentation_model.request_subscribe(self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.SUBSCRIBE_NO_BRANCHES_AVAILABLE)

    def test_shouldCallMessageSenderIfNoBranchesAvailableForSubscriptionBecauseUserAlreadySubscribedToThem(self):
        branch = "default"
        self._merge_dispatcher.get_all_branches.return_value = [branch]
        self._merge_dispatcher.get_branches_user_not_subscribed_to.return_value = []
        self._presentation_model.request_subscribe(self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.SUBSCRIBE_SUBSCRIBED_TO_BRANCHES_MESSAGE)

    def test_shouldCallMessageSenderWithBranchSelectorIfMultipleBranchesAvailable(self):
        branches = ["default", "release", "something_else"]
        self._merge_dispatcher.get_branches_user_not_subscribed_to.return_value = branches
        self._presentation_model.request_subscribe(self._identifier)
        self._message_sender.send_branch_selector.assert_called_once_with(self._identifier,
                                                                          States.subscribe,
                                                                          Messages.SUBSCRIBE_SELECT_BRANCH_MESSAGE,
                                                                          branches)

    def test_shouldSubscribeToSelectedBranch(self):
        self._presentation_model.request_subscribe(self._identifier, self._branch)
        self._merge_dispatcher.subscribe.assert_called_once_with(self._identifier, self._branch)

    def test_shouldCallMessageSenderIfSubscribeWasAllowed(self):
        self._merge_dispatcher.subscribe.return_value = SubscribeRequestStatus.subscription_complete
        self._presentation_model.request_subscribe(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.SUBSCRIBE_COMPLETE_MESSAGE.format(self._branch))

    def test_shouldCallMessageSenderIfUserAlreadySubscribed(self):
        self._merge_dispatcher.subscribe.return_value = SubscribeRequestStatus.already_subscribed
        self._presentation_model.request_subscribe(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.SUBSCRIBE_ALREADY_SUBSCRIBED_MESSAGE.
                                                          format(self._branch))

    def test_shouldCallMessageSenderIfSubscribeWasCalledButBranchAreNotExist(self):
        self._merge_dispatcher.subscribe.return_value = SubscribeRequestStatus.branch_not_exist
        self._presentation_model.request_subscribe(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.SUBSCRIBE_BRANCH_NOT_EXIST_MESSAGE.
                                                          format(self._branch))


class BotPresentationModelUnsubscribeTest(unittest.TestCase):
    def setUp(self):
        self._branch = "default"
        self._merge_dispatcher = create_autospec(Dispatcher)
        self._merge_dispatcher.get_branches_user_subscribed_to.return_value = [self._branch]
        self._message_sender = create_autospec(MessageSender)
        self._users_holder = create_autospec(BotModel)
        self._presentation_model = BotPresentationModel(self._merge_dispatcher, self._message_sender)

        self._identifier = 123456

    def tearDown(self):
        self._presentation_model = None

    def test_shouldAskCollectionWithBranchesPossibleToUnsubscribe(self):
        branch_filter = "filter"
        self._presentation_model.request_unsubscribe(self._identifier, branch_filter=branch_filter)
        self._merge_dispatcher.get_branches_user_subscribed_to.assert_called_once_with(self._identifier, branch_filter)

    def test_shouldShowMessageIfNoBranchesAvailable(self):
        self._merge_dispatcher.get_all_branches.return_value = []
        self._merge_dispatcher.get_branches_user_subscribed_to.return_value = []
        self._presentation_model.request_unsubscribe(self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.UNSUBSCRIBE_NO_BRANCHES_AVAILABLE)

    def test_shouldCallMessageSenderIfNoBranchesAvailableForSubscriptionBecauseUserNotSubscribedToThem(self):
        branch = "default"
        self._merge_dispatcher.get_all_branches.return_value = [branch]
        self._merge_dispatcher.get_branches_user_subscribed_to.return_value = []
        self._presentation_model.request_unsubscribe(self._identifier)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.UNSUBSCRIBE_NOT_IN_BRANCHES_MESSAGE)

    def test_shouldCallMessageSenderWithBranchSelectorIfMultipleBranchesAvailable(self):
        branches = ["default", "release", "something_else"]
        self._merge_dispatcher.get_branches_user_subscribed_to.return_value = branches
        self._presentation_model.request_unsubscribe(self._identifier)
        self._message_sender.send_branch_selector.assert_called_once_with(self._identifier,
                                                                          States.unsubscribe,
                                                                          Messages.UNSUBSCRIBE_SELECT_BRANCH_MESSAGE,
                                                                          branches)

    def test_shouldUnsubscribeFromSelectedBranch(self):
        self._presentation_model.request_unsubscribe(self._identifier, self._branch)
        self._merge_dispatcher.unsubscribe.assert_called_once_with(self._identifier, self._branch)

    def test_shouldCallMessageSenderIfUnsubscribeWasAllowed(self):
        self._merge_dispatcher.unsubscribe.return_value = UnsubscribeRequestStatus.unsubscription_complete
        self._presentation_model.request_unsubscribe(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.UNSUBSCRIBE_COMPLETE_MESSAGE.format(self._branch))

    def test_shouldCallMessageSenderIfUserNotSubscribed(self):
        self._merge_dispatcher.unsubscribe.return_value = UnsubscribeRequestStatus.user_not_in_branch
        self._presentation_model.request_unsubscribe(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.UNSUBSCRIBE_NOT_SUBSCRIBED_MESSAGE.
                                                          format(self._branch))

    def test_shouldCallMessageSenderIfUnsubscribeWasCalledButBranchAreNotExist(self):
        self._merge_dispatcher.unsubscribe.return_value = UnsubscribeRequestStatus.branch_not_exist
        self._presentation_model.request_unsubscribe(self._identifier, self._branch)
        self._message_sender.send.assert_called_once_with(self._identifier,
                                                          Messages.UNSUBSCRIBE_BRANCH_NOT_EXIST_MESSAGE.
                                                          format(self._branch))


class BotPresentationModelNotifierTest(unittest.TestCase):
    def setUp(self):
        self._branch = "default"
        self._message_sender = create_autospec(MessageSender)
        self._users_holder = create_autospec(BotModel)
        self._presentation_model = BotPresentationModel(create_autospec(Dispatcher), self._message_sender)

        self._whom_user_id = 123456
        self._whom_user = User("Jack Daniels", self._whom_user_id)
        self._users_holder.get_identifier.return_value = self._whom_user_id
        self._action_user = User("Johnny Walker", 787878)
        self._kicked_user = User("Jameson", 984512)

    def tearDown(self):
        self._presentation_model = None

    @staticmethod
    def generate_message(action_user, branch, action):
        action_text = ""
        if action == NotifierActions.starts_merge:
            action_text = "has started merge"
        elif action == NotifierActions.joins_queue:
            action_text = "has joined queue for merge"
        elif action == NotifierActions.cancels_merge:
            action_text = "has cancelled merge"
        elif action == NotifierActions.exits_queue:
            action_text = "has exited queue for merge"
        elif action == NotifierActions.done_merge:
            action_text = "has finished merge"
        return "<i>" + action_user.get_name() + "</i> " + action_text + " to branch <b>" + branch + "</b>."

    def test_shouldSendMessageIfMergeStarted(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.starts_merge,
                                        Notifier.ActionData(self._action_user, self._branch))
        message = self.generate_message(self._action_user, self._branch, NotifierActions.starts_merge)
        self._message_sender.send.assert_called_once_with(self._whom_user_id, message)

    def test_shouldNotSendMessageIfUserReadyToMerge(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.ready_to_merge,
                                        Notifier.ActionData(self._action_user, self._branch))
        self._message_sender.send.assert_not_called()

    def test_shouldSendMessageIfUserJoinsQueue(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.joins_queue,
                                        Notifier.ActionData(self._action_user, self._branch))
        message = self.generate_message(self._action_user, self._branch, NotifierActions.joins_queue)
        self._message_sender.send.assert_called_once_with(self._whom_user_id, message)

    def test_shouldSendMessageIfUserCancelsMerge(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.cancels_merge,
                                        Notifier.ActionData(self._action_user, self._branch))
        message = self.generate_message(self._action_user, self._branch, NotifierActions.cancels_merge)
        self._message_sender.send.assert_called_once_with(self._whom_user_id, message)

    def test_shouldSendMessageIfUserExitsQueue(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.exits_queue,
                                        Notifier.ActionData(self._action_user, self._branch))
        message = self.generate_message(self._action_user, self._branch, NotifierActions.exits_queue)
        self._message_sender.send.assert_called_once_with(self._whom_user_id, message)

    def test_shouldSendMessageIfUserFinishedMerge(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.done_merge,
                                        Notifier.ActionData(self._action_user, self._branch))
        message = self.generate_message(self._action_user, self._branch, NotifierActions.done_merge)
        self._message_sender.send.assert_called_once_with(self._whom_user_id, message)

    def test_shouldSendMessageIfMergeStartedBySameUserAsSender(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.starts_merge,
                                        Notifier.ActionData(self._whom_user, self._branch))
        message = str.format(Messages.ACTION_MESSAGE_STARTED_MERGE, self._branch)
        self._message_sender.send.assert_called_once_with(self._whom_user_id, message)

    def test_shouldSendMessageIfUserReadyToMerge(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.ready_to_merge,
                                        Notifier.ActionData(self._whom_user, self._branch))
        message = str.format(Messages.ACTION_MESSAGE_YOUR_MERGE_TURN, self._branch)
        self._message_sender.request_merge_confirmation.assert_called_once_with(self._whom_user_id, message,
                                                                                self._branch)

    def test_shouldNotSendMessageIfSameUserAsSenderJoinsQueue(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.joins_queue,
                                        Notifier.ActionData(self._whom_user, self._branch))
        self._message_sender.send.assert_not_called()

    def test_shouldNotSendMessageIfSameUserAsSenderCancelsMerge(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.cancels_merge,
                                        Notifier.ActionData(self._whom_user, self._branch))
        self._message_sender.send.assert_not_called()

    def test_shouldNotSendMessageIfSameUserAsSenderExitsQueue(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.exits_queue,
                                        Notifier.ActionData(self._whom_user, self._branch))
        self._message_sender.send.assert_not_called()

    def test_shouldNotSendMessageIfSameUserAsSenderFinishedMerge(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.done_merge,
                                        Notifier.ActionData(self._whom_user, self._branch))
        self._message_sender.send.assert_not_called()

    def test_shouldSendMessageIfSomeoneKickedUser(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.kicks_user,
                                        Notifier.KickActionData(self._action_user, self._branch, self._kicked_user))
        message = str.format("<i>{0}</i> has kicked {1} from branch <b>{2}</b>. Even I shocked by this cruelty.",
                             self._action_user.get_name(), self._kicked_user.get_name(), self._branch)
        self._message_sender.send.assert_called_once_with(self._whom_user_id, message)

    def test_shouldSendMessageIfSomeoneKickedYou(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.kicks_user,
                                        Notifier.KickActionData(self._action_user, self._branch, self._whom_user))
        message = str.format("<i>{0}</i> has kicked you from branch <b>{1}</b>. Nothing personal, only business.",
                             self._action_user.get_name(), self._branch)
        self._message_sender.send.assert_called_once_with(self._whom_user_id, message)

    def test_shouldSendMessageIfSomeoneKickedHimself(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.kicks_himself,
                                        Notifier.KickActionData(self._action_user, self._branch, self._action_user))
        message = str.format("<i>{0}</i> has kicked himself from branch <b>{1}</b>. What a strange way for suicide.",
                             self._action_user.get_name(), self._branch)
        self._message_sender.send.assert_called_once_with(self._whom_user_id, message)

    def test_shouldSendMessageIfYouKickedYourself(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.kicks_himself,
                                        Notifier.KickActionData(self._whom_user, self._branch, self._whom_user))
        message = str.format("You've kicked yourself from branch <b>{}</b>. Tell me, are you alright? Next "
                             "time use /cancel command, it much more effective.", self._branch)
        self._message_sender.send.assert_called_once_with(self._whom_user_id, message)

    def test_shouldSendMessageIfYouWasPushedAwayByMergeFix(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.starts_fix,
                                        Notifier.MergeFixActionData(self._action_user, self._branch, self._whom_user))
        message = str.format(Messages.ACTION_MESSAGE_PUSH_BACK, self._action_user.get_name(), self._branch)
        self._message_sender.send.assert_called_once_with(self._whom_user_id, message)

    def test_shouldSendMessageIfSomeoneStartedMergeFixInYourQueue(self):
        self._presentation_model.notify(self._whom_user, NotifierActions.starts_fix,
                                        Notifier.MergeFixActionData(self._action_user, self._branch, None))
        message = str.format(Messages.ACTION_MESSAGE_STARTS_FIX, self._action_user.get_name(), self._branch)
        self._message_sender.send.assert_called_once_with(self._whom_user_id, message)


class BotPresentationModelModelManagementTest(unittest.TestCase):
    def setUp(self):
        self._dispatcher = create_autospec(Dispatcher)
        self._presentation_model = BotPresentationModel(self._dispatcher, create_autospec(MessageSender))

    def tearDown(self):
        self._dispatcher = None
        self._presentation_model = None

    def test_shouldDelegateUserUpdateToMergeDispatcher(self):
        identifier = 123
        first_name = "Jack"
        second_name = "Daniels"
        self._presentation_model.update_user(identifier, first_name, second_name)
        self._dispatcher.update_user.assert_any_call(identifier, first_name, second_name)
