import markdown
import nh3
from markupsafe import Markup
from datetime import datetime, timezone
import re

def md_to_html(text: str) -> Markup:
    """
    Convert Markdown to sanitized HTML using pymdown-extensions.
    Full GitHub-flavored support + single newlines → <br>.
    """
    if not text:
        return Markup("")

    # === PyMdown Extensions ===
    extensions = [
        "nl2br",                    # Single newline → <br>
        "tables",
        "toc",                      # Table of Contents
        "attr_list",                # {.class #id}
        "footnotes",

        # PyMdown extensions
        "pymdownx.highlight",       # Syntax highlighting
        "pymdownx.superfences",     # Advanced code blocks
        "pymdownx.tasklist",        # - [x] Checkboxes
        "pymdownx.tilde",           # ~~strikethrough~~ and ~subscript~
        "pymdownx.magiclink",       # Auto-link URLs/emails
        "pymdownx.betterem",        # Improved **bold** and _italic_
    ]

    extension_configs = {
        "pymdownx.highlight": {
            "css_class": "highlight",
            "linenums": False,          # Change to True for line numbers
        },
        "pymdownx.tasklist": {
            "custom_checkbox": True,
        },
        "pymdownx.superfences": {
            "disable_indented_code_blocks": True,
        },
        "pymdownx.tilde": {
            "subscript": False,         # Set True if you want ~subscript~
        },
    }

    html = markdown.markdown(
        text,
        extensions=extensions,
        extension_configs=extension_configs,
        output_format="html5",
    )

    # === Sanitization ===
    allowed_tags = {
        "h1", "h2", "h3", "h4", "h5", "h6",
        "p", "br", "strong", "em", "del", "ins",
        "ul", "ol", "li",
        "blockquote", "hr",
        "code", "pre",
        "table", "thead", "tbody", "tr", "th", "td",
        "a", "img",
        "span", "div", "sup", "sub", "details", "summary",
        "input",                    # Task list checkboxes
    }

    allowed_attrs = {
        "*": {"class", "id", "title"},
        "a": {"href", "title", "target"},
        "img": {"src", "alt", "title", "width", "height"},
        "th": {"align"},
        "td": {"align"},
        "input": {"type", "checked", "disabled"},
    }

    cleaned_html = nh3.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attrs,
        link_rel="noopener noreferrer",
    )

    return Markup(cleaned_html)

def human_readable_date(date_str):
    now = datetime.now(timezone.utc)

    # If the input dt is naive, you may need to give it a timezone:
    if date_str.tzinfo is None:
        date_str = date_str.replace(tzinfo=timezone.utc)
    diff = now - date_str
    print(f"Now: {now}")
    print(f"Date: {date_str}")
    print(f"Diff: {diff}")
    
    seconds = diff.total_seconds()
    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = diff.days
    weeks = int(days // 7)
    months = int(days // 30)
    years = int(days // 365)
    
    if seconds < 60:
        return 'Just now'
    elif minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif days < 7:
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif weeks < 4:
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif months < 12:
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        return f"{years} year{'s' if years != 1 else ''} ago"
    
    