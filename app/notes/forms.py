from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from app.models import Note

class NoteForm(FlaskForm):
    title = StringField('Title')
    content = TextAreaField('Content', render_kw={
        "placeholder": "Start typing here...\nThink better, write better."
    })
    save = SubmitField('Save')