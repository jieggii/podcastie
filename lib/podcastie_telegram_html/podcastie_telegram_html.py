class Link:
    text: str
    url: str | None

    def __init__(self, text: str, url: str | None = None):
        self.text = text
        self.url = url

    def compile(self) -> str:
        """
        Compiles the hyperlink into an HTML anchor tag if a URL is provided, otherwise returns the text.
        """
        if self.url:
            return f'<a href="{self.url}">{self.text}</a>'
        return self.text
