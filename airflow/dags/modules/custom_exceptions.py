class TwitterAPIError(Exception):
    """Exception raised for errors while calling Twitter API.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Error: Something went wrong while trying authenticate on Twitter API."):
        self.message = message
        super().__init__(self.message)


class TwitterAuthorizationError(Exception):
    """Exception raised for errors while calling Cursor to fetch tweets.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Error: Something went wrong trying to authorizing your request, check your credentials and try again."):
        self.message = message
        super().__init__(self.message)


class TwitterNoPostsFound(Exception):
    """Exception raised for errors while filtering Twitter posts.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Sorry, we didn't find anything matching your search."):
        self.message = message
        super().__init__(self.message)


class TwitterAPIUnavailable(Exception):
    """Exception raised while API is not available

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Error: It seems the API is no longer avaiable."):
        self.message = message
        super().__init__(self.message)


class KeywordNotFound(Exception):
    """Exception raised when not keyword or hashtag is provided to the app.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="Error: Please provide at least one word or hashtag."):
        self.message = message
        super().__init__(self.message)
