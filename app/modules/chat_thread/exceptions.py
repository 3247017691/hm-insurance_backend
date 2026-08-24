from app.core.exceptions import ApplicationError


class ChatThreadNotFoundError(ApplicationError):
    """非当前用户的会话或会话不存在"""

    status_code = 400
    code = 'CHAT_THREAD_NOT_FOUND'
    message = '会话不存在或不属于当前用户'