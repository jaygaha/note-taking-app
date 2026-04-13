import markdown
import bleach
from markupsafe import Markup
from datetime import datetime, timezone
import re

def md_to_html(text):
    if not text:
        return ""
    
    # Replace blank lines with <br>
    text = re.sub(r'\n\s*\n', '\n\n&nbsp;\n\n', text)

    # Convert Markdown to HTML
    extensions = [
        'extra', 
        'fenced_code', 
        'codehilite', 
        'nl2br'
    ]
    # 'extra' enables tables, footnotes, and abbreviations
    # 'fenced_code' enables triple-backtick code blocks
    html = markdown.markdown(text, extensions=extensions)
    
    # Sanitize HTML (Allow only safe tags)
    allowed_tags = [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'strong', 'em', 
        'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'hr'
    ]
    cleaned_html = bleach.clean(html, tags=allowed_tags)
    
    # Mark as safe for Jinja2 rendering
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
    
    