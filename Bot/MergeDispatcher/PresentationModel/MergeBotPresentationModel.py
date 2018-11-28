from enum import Enum

from Bot.MergeDispatcher import CancelRequestStatus
from Bot.MergeDispatcher import Dispatcher
from Bot.MergeDispatcher import DoneRequestStatus
from Bot.MergeDispatcher import FixRequestStatus
from Bot.MergeDispatcher import KickRequestStatus
from Bot.MergeDispatcher import MergeRequestStatus
from Bot.MergeDispatcher import Notifier
from Bot.MergeDispatcher import NotifierActions
from Bot.MergeDispatcher import SubscribeRequestStatus
from Bot.MergeDispatcher import UnsubscribeRequestStatus


class States(Enum):
    merge = 0
    cancel = 1
    done = 2
    queue = 3
    kick = 4
    fix = 5
    confirm = 6
    subscribe = 7
    unsubscribe = 8


class Messages:
    MERGE_NO_BRANCHES_AVAILABLE = "No branches with given name are available for merge requests.\n" \
                                  "Check name and try again, or use /merge command without parameters and select " \
                                  "branch from the list."
    MERGE_SELECT_BRANCH_MESSAGE = "Select branch for <i>merge</i> command:"
    MERGE_ADDED_TO_QUEUE_MESSAGE = "&#x1F51C You're <b>{}</b> in queue for merge in branch <b>{}</b>.\n" \
                                   "You'll be informed when it's your turn to merge."
    MERGE_ALREADY_IN_QUEUE_MESSAGE = "You're already in queue for branch <b>{}</b>. Calm down."
    MERGE_BRANCH_NOT_EXIST_MESSAGE = "You're trying to merge in non-existing branch <b>{}</b>."

    CANCEL_NO_BRANCHES_AVAILABLE = "No branches are available for <i>cancel</i> command.\n" \
                                   "Are you sure that you've done merge requests already?"
    CANCEL_SELECT_BRANCH_MESSAGE = "Select branch for <i>cancel</i> command:"
    CANCEL_MERGE_CANCELLED_MESSAGE = "You've cancelled merge to branch <b>{}</b>. Coward."
    CANCEL_EXITED_FROM_QUEUE_MESSAGE = "You've exited merge queue for branch <b>{}</b>. Is it 19 o'clock already?"
    CANCEL_BRANCH_NOT_EXIST_MESSAGE = "You're trying to cancel merge in non-existing branch <b>{}</b>."
    CANCEL_NOT_IN_QUEUE_MESSAGE = "You're trying to cancel merge in <b>{}</b>, " \
                                  "but you are not in queue for this branch."

    DONE_NO_BRANCHES_AVAILABLE = "No branches are available for <i>done</i> command.\n" \
                                 "Are you sure that you have active merges in some branches?\n" \
                                 "Remember, you can't finish merge with <i>done</i> command if you're in queue, but " \
                                 "haven't started merge yet."
    DONE_SELECT_BRANCH_MESSAGE = "Select branch for <i>done</i> command:"
    DONE_MERGE_DONE_MESSAGE = "You've done merge to branch <b>{}</b>. Hooray."
    DONE_NOT_YOUR_TURN_MESSAGE = "You can't finish merge in <b>{}</b>, it's not your turn to merge in " \
                                 "this branch."
    DONE_BRANCH_NOT_EXIST_MESSAGE = "You're trying to finish merge in non-existing branch <b>{}</b>. Nice try."

    QUEUE_NO_BRANCHES_AVAILABLE = "Sorry, for now no branches with given name available for queue info requests."
    QUEUE_SELECT_BRANCH_MESSAGE = "Select branch for the queue info:"
    QUEUE_EMPTY_INFO_MESSAGE = "Queue for branch <b>{}</b> is empty."
    QUEUE_INFO_MESSAGE = "Queue information for branch <b>{}</b>:{}"
    QUEUE_INFO_USER_IN_MERGE = "\n- <b>{} (in merge)</b>"
    QUEUE_INFO_CURRENT_USER_IN_QUEUE = "\n- <i>{} (you)</i>"
    QUEUE_INFO_CURRENT_USER_IN_MERGE = "\n- <b>{} (in merge, you)</b>"
    QUEUE_INFO_USER_IN_QUEUE = "\n- {}"
    QUEUE_BRANCH_NOT_EXIST_MESSAGE = "You're trying to get queue information from non-existing " \
                                     "branch <b>{}</b>. Strange desire."

    KICK_NO_BRANCHES_AVAILABLE = "No branches with given name available for <i>kick</i> command"
    KICK_SELECT_BRANCH_MESSAGE = "Choose branch from which you want to kick someone:"
    KICK_NO_USERS_TO_KILL = "Sorry, no users in this queue. But I am pretty sure, that you will find whom to kick in " \
                            "other queues!"
    KICK_BRANCH_NOT_EXIST = "I can't believe, but looks like my internal state is broken, and branch <b>{}</b> " \
                            "does not exist. Please, show this message to my creator. He definitely will not be happy."
    KICK_USER_NOT_IN_BRANCH = "I can't find user <b>{0}</b> in branch <b>{1}</b>. Looks like this time he is escaped."
    KICK_USER_NOT_EXIST = "I can't find user with given ID in my database. This is a really strange thing, " \
                          "I have not had amnesia before. Please, show this message to my creator."
    KICK_USER_WAS_KICKED = "You've kicked user. What do you feel? Nothing?\nYou, people, are much worse than we are."
    KICK_SELECT_USER = "So, who is the weakest link?"

    FIX_NO_BRANCHES_AVAILABLE = "No branches with given name available for <i>fix</i> command"
    FIX_SELECT_BRANCH_MESSAGE = "Choose the branch you want to fix:"
    FIX_MERGE_ALLOWED_MESSAGE = "You're allowed to start fixing of branch <b>{}</b>."
    FIX_ALREADY_IN_MERGE_MESSAGE = "You're already in merge to branch <b>{}</b>, and you really do not need to " \
                                   "do something until you finish."
    FIX_BRANCH_NOT_EXIST_MESSAGE = "You're trying to merge fix in non-existing branch <b>{}</b>. I guess, that " \
                                   "Narnia needs your patch too."

    SUBSCRIBE_NO_BRANCHES_AVAILABLE = "No branches available for your subscribe request. Looks like there are " \
                                      "no branches with name like you want."
    SUBSCRIBE_SUBSCRIBED_TO_BRANCHES_MESSAGE = "Looks like you already have subscribed to all the branches, " \
                                               "suitable for your request."
    SUBSCRIBE_SELECT_BRANCH_MESSAGE = "Select branch you want subscribe to:"
    SUBSCRIBE_COMPLETE_MESSAGE = "You have successfully subscribed to branch <b>{}</b>."
    SUBSCRIBE_ALREADY_SUBSCRIBED_MESSAGE = "You have tried to subscribe to branch <b>{}</b>, but you are already " \
                                           "subscribed."
    SUBSCRIBE_BRANCH_NOT_EXIST_MESSAGE = "You have tried to subscribe to updates in branch <b>{}</b>, but this " \
                                         "branch does not exist."

    UNSUBSCRIBE_NO_BRANCHES_AVAILABLE = "No branches available for your unsubscribe request. Looks like you have " \
                                        "not subscribed to any branch yet."
    UNSUBSCRIBE_NOT_IN_BRANCHES_MESSAGE = "Looks like you not subscribed to any branch, suitable for your " \
                                          "request."
    UNSUBSCRIBE_SELECT_BRANCH_MESSAGE = "Select branch you want unsubscribe from:"
    UNSUBSCRIBE_COMPLETE_MESSAGE = "You have successfully unsubscribed from branch <b>{}</b>."
    UNSUBSCRIBE_NOT_SUBSCRIBED_MESSAGE = "You have tried to unsubscribe from branch <b>{}</b>, but you are not " \
                                         "subscribed."
    UNSUBSCRIBE_BRANCH_NOT_EXIST_MESSAGE = "You have tried to unsubscribe from updates in branch <b>{}</b>, but this " \
                                           "branch does not exist."

    CONFIRM_MERGE_FAILED_MESSAGE = "You have failed to confirm your merge. It is possible, that you was kicked " \
                                   "by another user, or someone have started merging of the fix, but if you believe, " \
                                   "that your friends can't do things like that " \
                                   "(huh), you can tell about this error to administrator."

    ACTION_TEXT_MERGE_STARTED = "has started merge"
    ACTION_TEXT_QUEUE_JOINED = "has joined queue for merge"
    ACTION_TEXT_MERGE_CANCELLED = "has cancelled merge"
    ACTION_TEXT_EXITED_QUEUE = "has exited queue for merge"
    ACTION_TEXT_MERGE_FINISHED = "has finished merge"

    ACTION_MESSAGE_GENERIC = "<i>{0}</i> {1} to branch <b>{2}</b>."
    ACTION_MESSAGE_KICKED_USER = "<i>{0}</i> has kicked {1} from branch <b>{2}</b>. Even I shocked by this cruelty."
    ACTION_MESSAGE_KICKED_YOU = "<i>{0}</i> has kicked you from branch <b>{1}</b>. Nothing personal, only business."
    ACTION_MESSAGE_KICKED_SELF = "<i>{0}</i> has kicked himself from branch <b>{1}</b>. What a strange way for suicide."

    ACTION_MESSAGE_PUSH_BACK = "User <i>{0}</i> has pushed you back to queue of branch <b>{1}</b> and started a " \
                               "merge of fix into it. I hope he at least told you about it."
    ACTION_MESSAGE_STARTS_FIX = "User <i>{0}</i> has started merge of fix to branch <b>{1}</b>. Wish him luck."

    ACTION_MESSAGE_YOU_KICKED_SELF = "You've kicked yourself from branch <b>{}</b>. Tell me, are you alright? Next " \
                                     "time use /cancel command, it much more effective."
    ACTION_MESSAGE_STARTED_MERGE = "&#x2705 You've started the merge to branch <b>{}</b>. Do not fail the build, OK?"
    ACTION_MESSAGE_YOUR_MERGE_TURN = "&#x1F514 It is now your turn to merge in branch <b>{}</b>. Press 'Confirm' " \
                                     "button to start merge or 'Cancel' button to free queue."


class MessageSender:
    class Payload:
        def __init__(self, branch=None):
            self._branch = branch

        def __eq__(self, other):
            return type(self) == type(other) and \
                   self._branch == other.get_branch()

        def __ne__(self, other):
            return not self == other

        def __str__(self):
            return str.format("Payload: branch={0}", self._branch)

        def get_branch(self):
            return self._branch

    def send(self, identifier: int, message: str) -> None:
        raise NotImplementedError

    def send_branch_selector(self, identifier: int, state: States, message: str, branches: list,
                             payload: Payload = None) -> None:
        raise NotImplementedError

    def send_user_selector(self, identifier: int, state: States, message: str, users: list,
                           payload: Payload = None) -> None:
        raise NotImplementedError

    def request_merge_confirmation(self, identifier: int, message: str, branch: str) -> None:
        raise NotImplementedError


class BotPresentationModel(Notifier):
    def __init__(self, merge_dispatcher: Dispatcher, message_sender: MessageSender):
        self._merge_dispatcher = merge_dispatcher
        self._message_sender = message_sender
        self._merge_dispatcher.set_notifier(self)
        self._merge_dispatcher.prepare()

    def confirm_merge(self, user_id, branch):
        result = self._merge_dispatcher.confirm_merge(user_id, branch)
        if not result:
            self._message_sender.send(user_id, Messages.CONFIRM_MERGE_FAILED_MESSAGE.format(branch))

    def request_merge(self, user_id, branch_filter=None) -> None:
        branches = self._merge_dispatcher.get_all_branches(branch_filter)
        if len(branches) == 0:
            self._message_sender.send(user_id, Messages.MERGE_NO_BRANCHES_AVAILABLE)
        elif len(branches) == 1:
            branch = branches[0]
            result = self._merge_dispatcher.merge(user_id, branch)
            message = None
            if result == MergeRequestStatus.merge_requested:
                queue_info = self._merge_dispatcher.get_branch_queue_info(branch)
                persons_in_queue = len(queue_info.users_queue) + (1 if queue_info.active_user is not None else 0)
                persons_in_queue_str = "{0}{1}".format(str(persons_in_queue),
                                                       'th' if 10 <= persons_in_queue % 100 < 20 else
                                                       {1: 'st', 2: 'nd', 3: 'rd'}.get(persons_in_queue % 10, "th"))

                message = Messages.MERGE_ADDED_TO_QUEUE_MESSAGE.format(persons_in_queue_str, branch)
            elif result == MergeRequestStatus.already_in_queue:
                message = Messages.MERGE_ALREADY_IN_QUEUE_MESSAGE.format(branch)
            elif result == MergeRequestStatus.branch_not_exist:
                message = Messages.MERGE_BRANCH_NOT_EXIST_MESSAGE.format(branch)
            if message is not None:
                self._message_sender.send(user_id, message)
        else:
            self._message_sender.send_branch_selector(user_id, States.merge, Messages.MERGE_SELECT_BRANCH_MESSAGE,
                                                      branches)

    def request_cancel(self, user_id, branch_filter=None) -> None:
        branches = self._merge_dispatcher.get_all_branches_with_user(user_id, branch_filter)
        if len(branches) == 0:
            self._message_sender.send(user_id, Messages.CANCEL_NO_BRANCHES_AVAILABLE)
        elif len(branches) == 1:
            branch = branches[0]
            result = self._merge_dispatcher.cancel(user_id, branch)
            message = None
            if result == CancelRequestStatus.merge_cancelled:
                message = Messages.CANCEL_MERGE_CANCELLED_MESSAGE.format(branch)
            elif result == CancelRequestStatus.exited_from_queue:
                message = Messages.CANCEL_EXITED_FROM_QUEUE_MESSAGE.format(branch)
            elif result == CancelRequestStatus.branch_not_exist:
                message = Messages.CANCEL_BRANCH_NOT_EXIST_MESSAGE.format(branch)
            elif result == CancelRequestStatus.not_in_queue:
                message = Messages.CANCEL_NOT_IN_QUEUE_MESSAGE.format(branch)
            if message is not None:
                self._message_sender.send(user_id, message)
        else:
            self._message_sender.send_branch_selector(user_id, States.cancel, Messages.CANCEL_SELECT_BRANCH_MESSAGE,
                                                      branches)

    def request_done(self, user_id, branch_filter=None) -> None:
        branches = self._merge_dispatcher.get_active_user_branches(user_id, branch_filter)
        if len(branches) == 0:
            self._message_sender.send(user_id, Messages.DONE_NO_BRANCHES_AVAILABLE)
        elif len(branches) == 1:
            branch = branches[0]
            result = self._merge_dispatcher.done(user_id, branch)
            message = None
            if result == DoneRequestStatus.merge_done:
                message = Messages.DONE_MERGE_DONE_MESSAGE.format(branch)
            elif result == DoneRequestStatus.user_not_active:
                message = Messages.DONE_NOT_YOUR_TURN_MESSAGE.format(branch)
            elif result == DoneRequestStatus.branch_not_exist:
                message = Messages.DONE_BRANCH_NOT_EXIST_MESSAGE.format(branch)
            if message is not None:
                self._message_sender.send(user_id, message)
        else:
            self._message_sender.send_branch_selector(user_id, States.done, Messages.DONE_SELECT_BRANCH_MESSAGE,
                                                      branches)

    def request_queue_info(self, user_id, branch_filter=None) -> None:
        branches = self._merge_dispatcher.get_all_branches(branch_filter)
        if len(branches) == 0:
            self._message_sender.send(user_id, Messages.QUEUE_NO_BRANCHES_AVAILABLE)
        elif len(branches) == 1:
            branch = branches[0]
            result = self._merge_dispatcher.get_branch_queue_info(branch)
            if result is not None:
                if result.active_user is None and not result.users_queue:
                    message = Messages.QUEUE_EMPTY_INFO_MESSAGE.format(branch)
                else:
                    users_list = str()
                    if result.active_user is not None:
                        if result.active_user.get_identifier() == user_id:
                            users_list = Messages.QUEUE_INFO_CURRENT_USER_IN_MERGE.format(result.active_user.get_name())
                        else:
                            users_list = Messages.QUEUE_INFO_USER_IN_MERGE.format(result.active_user.get_name())

                    for user_in_queue in result.users_queue:
                        if user_id != user_in_queue.get_identifier():
                            users_list += Messages.QUEUE_INFO_USER_IN_QUEUE.format(user_in_queue.get_name())
                        else:
                            users_list += Messages.QUEUE_INFO_CURRENT_USER_IN_QUEUE.format(user_in_queue.get_name())

                    message = Messages.QUEUE_INFO_MESSAGE.format(branch, users_list)
            else:
                message = Messages.QUEUE_BRANCH_NOT_EXIST_MESSAGE.format(branch)
            if message is not None:
                self._message_sender.send(user_id, message)
        else:
            self._message_sender.send_branch_selector(user_id, States.queue,
                                                      Messages.QUEUE_SELECT_BRANCH_MESSAGE, branches)

    def request_kick(self, user_id, branch_filter=None, kicked_user_id=None):
        branches = self._merge_dispatcher.get_all_branches(branch_filter)
        if len(branches) == 0:
            self._message_sender.send(user_id, Messages.KICK_NO_BRANCHES_AVAILABLE)
        elif len(branches) == 1:
            branch = branches[0]
            if kicked_user_id is None:
                result = self._merge_dispatcher.get_branch_queue_info(branch)
                if result is not None:
                    users_in_branch = []
                    if result.active_user is not None:
                        users_in_branch.append(result.active_user)
                    users_in_branch.extend(result.users_queue)
                    if users_in_branch:
                        self._message_sender.send_user_selector(user_id, States.kick, Messages.KICK_SELECT_USER,
                                                                users_in_branch, MessageSender.Payload(branch=branch))
                    else:
                        self._message_sender.send(user_id, Messages.KICK_NO_USERS_TO_KILL)
                else:
                    self._message_sender.send(user_id, Messages.KICK_BRANCH_NOT_EXIST.format(branch))
            else:
                result = self._merge_dispatcher.kick(user_id, kicked_user_id, branch)
                message = None
                if result == KickRequestStatus.user_kicked and user_id != kicked_user_id:
                    message = Messages.KICK_USER_WAS_KICKED
                elif result == KickRequestStatus.branch_not_exist:
                    message = Messages.KICK_BRANCH_NOT_EXIST.format(branch)
                elif result == KickRequestStatus.user_not_in_branch:
                    user = self._merge_dispatcher.get_user(kicked_user_id)
                    if user is not None:
                        message = Messages.KICK_USER_NOT_IN_BRANCH.format(user.get_name(), branch)
                    else:
                        message = Messages.KICK_USER_NOT_EXIST
                if message is not None:
                    self._message_sender.send(user_id, message)
        else:
            self._message_sender.send_branch_selector(user_id, States.kick,
                                                      Messages.KICK_SELECT_BRANCH_MESSAGE, branches)

    def request_fix(self, user_id, branch_filter=None) -> None:
        branches = self._merge_dispatcher.get_all_branches(branch_filter)
        if len(branches) == 0:
            self._message_sender.send(user_id, Messages.FIX_NO_BRANCHES_AVAILABLE)
        elif len(branches) == 1:
            branch = branches[0]
            result = self._merge_dispatcher.fix(user_id, branch)
            message = None
            if result == FixRequestStatus.fix_allowed:
                message = Messages.FIX_MERGE_ALLOWED_MESSAGE.format(branch)
            elif result == FixRequestStatus.user_already_in_merge:
                message = Messages.FIX_ALREADY_IN_MERGE_MESSAGE.format(branch)
            elif result == FixRequestStatus.branch_not_exist:
                message = Messages.FIX_BRANCH_NOT_EXIST_MESSAGE.format(branch)
            if message is not None:
                self._message_sender.send(user_id, message)
        else:
            self._message_sender.send_branch_selector(user_id, States.fix,
                                                      Messages.FIX_SELECT_BRANCH_MESSAGE, branches)

    def request_subscribe(self, user_id, branch_filter=None) -> None:
        branches = self._merge_dispatcher.get_branches_user_not_subscribed_to(user_id, branch_filter)
        if len(branches) == 0:
            all_branches = self._merge_dispatcher.get_all_branches(branch_filter)
            if len(all_branches) > 0:
                self._message_sender.send(user_id, Messages.SUBSCRIBE_SUBSCRIBED_TO_BRANCHES_MESSAGE)
            else:
                self._message_sender.send(user_id, Messages.SUBSCRIBE_NO_BRANCHES_AVAILABLE)
        elif len(branches) == 1:
            branch = branches[0]
            result = self._merge_dispatcher.subscribe(user_id, branch)
            message = None
            if result == SubscribeRequestStatus.subscription_complete:
                message = Messages.SUBSCRIBE_COMPLETE_MESSAGE.format(branch)
            elif result == SubscribeRequestStatus.already_subscribed:
                message = Messages.SUBSCRIBE_ALREADY_SUBSCRIBED_MESSAGE.format(branch)
            elif result == SubscribeRequestStatus.branch_not_exist:
                message = Messages.SUBSCRIBE_BRANCH_NOT_EXIST_MESSAGE.format(branch)
            if message is not None:
                self._message_sender.send(user_id, message)
        else:
            self._message_sender.send_branch_selector(user_id, States.subscribe,
                                                      Messages.SUBSCRIBE_SELECT_BRANCH_MESSAGE, branches)

    def request_unsubscribe(self, user_id, branch_filter=None) -> None:
        branches = self._merge_dispatcher.get_branches_user_subscribed_to(user_id, branch_filter)
        if len(branches) == 0:
            all_branches = self._merge_dispatcher.get_all_branches(branch_filter)
            if len(all_branches) > 0:
                self._message_sender.send(user_id, Messages.UNSUBSCRIBE_NOT_IN_BRANCHES_MESSAGE)
            else:
                self._message_sender.send(user_id, Messages.UNSUBSCRIBE_NO_BRANCHES_AVAILABLE)
        elif len(branches) == 1:
            branch = branches[0]
            result = self._merge_dispatcher.unsubscribe(user_id, branch)
            message = None
            if result == UnsubscribeRequestStatus.unsubscription_complete:
                message = Messages.UNSUBSCRIBE_COMPLETE_MESSAGE.format(branch)
            elif result == UnsubscribeRequestStatus.user_not_in_branch:
                message = Messages.UNSUBSCRIBE_NOT_SUBSCRIBED_MESSAGE.format(branch)
            elif result == UnsubscribeRequestStatus.branch_not_exist:
                message = Messages.UNSUBSCRIBE_BRANCH_NOT_EXIST_MESSAGE.format(branch)
            if message is not None:
                self._message_sender.send(user_id, message)
        else:
            self._message_sender.send_branch_selector(user_id, States.unsubscribe,
                                                      Messages.UNSUBSCRIBE_SELECT_BRANCH_MESSAGE, branches)

    def notify(self, whom, action_type, action_data):
        if whom != action_data.get_user():
            action_text = None
            if action_type == NotifierActions.starts_merge:
                action_text = Messages.ACTION_TEXT_MERGE_STARTED
            elif action_type == NotifierActions.joins_queue:
                action_text = Messages.ACTION_TEXT_QUEUE_JOINED
            elif action_type == NotifierActions.cancels_merge:
                action_text = Messages.ACTION_TEXT_MERGE_CANCELLED
            elif action_type == NotifierActions.exits_queue:
                action_text = Messages.ACTION_TEXT_EXITED_QUEUE
            elif action_type == NotifierActions.done_merge:
                action_text = Messages.ACTION_TEXT_MERGE_FINISHED
            elif action_type == NotifierActions.kicks_user and whom != action_data.get_kicked_user():
                action_text = str.format(Messages.ACTION_MESSAGE_KICKED_USER, action_data.get_user().get_name(),
                                         action_data.get_kicked_user().get_name(), action_data.get_branch())
            elif action_type == NotifierActions.kicks_user and whom == action_data.get_kicked_user():
                action_text = str.format(Messages.ACTION_MESSAGE_KICKED_YOU, action_data.get_user().get_name(),
                                         action_data.get_branch())
            elif action_type == NotifierActions.kicks_himself:
                action_text = str.format(Messages.ACTION_MESSAGE_KICKED_SELF, action_data.get_user().get_name(),
                                         action_data.get_branch())
            elif action_type == NotifierActions.starts_fix and whom == action_data.get_pushed_user():
                action_text = str.format(Messages.ACTION_MESSAGE_PUSH_BACK, action_data.get_user().get_name(),
                                         action_data.get_branch())
            elif action_type == NotifierActions.starts_fix and whom != action_data.get_pushed_user():
                action_text = str.format(Messages.ACTION_MESSAGE_STARTS_FIX, action_data.get_user().get_name(),
                                         action_data.get_branch())

            if action_text is not None:
                if action_type != NotifierActions.kicks_user \
                        and action_type != NotifierActions.kicks_himself \
                        and action_type != NotifierActions.starts_fix:
                    message = str.format(Messages.ACTION_MESSAGE_GENERIC, action_data.get_user().get_name(),
                                         action_text, action_data.get_branch())
                else:
                    message = action_text
                self._message_sender.send(whom.get_identifier(), message)
        else:
            if action_type == NotifierActions.starts_merge:
                message = str.format(Messages.ACTION_MESSAGE_STARTED_MERGE, action_data.get_branch())
                self._message_sender.send(whom.get_identifier(), message)
            elif action_type == NotifierActions.ready_to_merge:
                message = str.format(Messages.ACTION_MESSAGE_YOUR_MERGE_TURN, action_data.get_branch())
                self._message_sender.request_merge_confirmation(whom.get_identifier(), message,
                                                                action_data.get_branch())
            elif action_type == NotifierActions.kicks_himself:
                message = str.format(Messages.ACTION_MESSAGE_YOU_KICKED_SELF, action_data.get_branch())
                self._message_sender.send(whom.get_identifier(), message)

    def update_user(self, identifier, first_name, last_name):
        self._merge_dispatcher.update_user(identifier, first_name, last_name)
