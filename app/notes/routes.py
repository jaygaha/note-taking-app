from flask import render_template, flash, redirect, url_for, request, Response, abort
from flask_login import login_required, current_user
from app import db, Config
from app.notes import notes_bp
from app.notes import forms
from app.models import Note
import random
import re
import io
import zipfile
from datetime import datetime, timezone


def _note_filename(note, ext='md'):
    """Build a filesystem-safe filename for a note, e.g. 'my-note-title-12.md'."""
    slug = re.sub(r'[^a-z0-9]+', '-', (note.title or 'untitled-note').lower()).strip('-')
    slug = slug or 'untitled-note'
    return f"{slug}-{note.id}.{ext}"


def _note_markdown(note):
    """Render a note as a standalone Markdown document (title as H1 + content)."""
    title = note.title or 'Untitled Note'
    return f"# {title}\n\n{note.content or ''}"

@notes_bp.route('/')
@login_required
def dashboard():
    # Process search query if present
    q = request.args.get('q', '').strip()
    query = Note.query.filter_by(user_id=current_user.id).filter(Note.deleted_at.is_(None))
    
    if q:
        search_term = f"%{q}%"
        query = query.filter(Note.title.ilike(search_term) | Note.content.ilike(search_term))
        
    # Get notes sorted by update time
    notes = query.order_by(Note.updated_at.desc()).all()

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    # Group notes by date
    grouped_notes = {}
    
    pinned_notes = [n for n in notes if n.is_pinned]
    unpinned_notes = [n for n in notes if not n.is_pinned]
    
    if pinned_notes:
        grouped_notes["Pinned"] = pinned_notes
        
    for n in unpinned_notes:
        dt = n.updated_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            
        diff_days = (now.date() - dt.date()).days
        
        if diff_days == 0:
            group_key = "Today"
        elif diff_days == 1:
            group_key = "Yesterday"
        elif diff_days < 7:
            group_key = "Previous 7 Days"
        elif diff_days < 30:
            group_key = "Previous 30 Days"
        else:
            group_key = dt.strftime("%B %Y")
            
        if group_key not in grouped_notes:
            grouped_notes[group_key] = []
        grouped_notes[group_key].append(n)

    # Random greeting
    first_name = current_user.full_name.split()[0] if current_user.full_name else 'there'
    greetings = [
        f"Hi, {first_name}",
        f"Hey {first_name} 👋",
        f"Good to see you, {first_name}",
        f"Howdy, {first_name}",
        f"Welcome back, {first_name}",
        f"What's on your mind, {first_name}?",
        f"Ready to write, {first_name}?",
    ]
    greeting = random.choice(greetings)

    # Query parameters
    task = request.args.get('task')
    note_id = request.args.get('note_id')
    # convert to int
    if note_id:
        note_id = int(note_id)
    
    welcome_card = True
    title = "Notes"
    form = None
    note = None # selected note
    selected_note_id = note_id

    # Show welcome page if no task or note_id is provided
    if task or note_id:
        welcome_card = False

    # Date in new title flag
    date_in_new_title = Config.DATE_IN_NEW_TITLE
    new_title = f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')} "

    # Request to create a new note
    if task == 'new':
        title = "New Note"
        form = forms.NoteForm()

    # Request to edit or preview a note
    if task == 'edit' or task == 'preview':
        title = f"{task.capitalize()} Note"
        note = Note.query.get_or_404(note_id)
        form = forms.NoteForm(obj=note)
        # Security check: Ensure the note belongs to the user
        if note.author != current_user:
            abort(403)
    

    # debug
    if Config.APP_ENV == 'development':
        print(f"task: {task}, note_id: {note_id}, welcome_card: {welcome_card}")

    return render_template(
        'notes/dashboard.html',
        notes=notes,
        grouped_notes=grouped_notes,
        title=title,
        app_shell=True,
        greeting=greeting,
        welcome_card=welcome_card,
        form=form,
        note=note,
        selected_note_id=selected_note_id,
        task=task,
        q=q,
        new_title=new_title if date_in_new_title else None
    )

@notes_bp.route('/save', methods=['POST', 'PUT'])
@login_required
def save():
    form = forms.NoteForm()
    
    if form.validate_on_submit():
        # Check if the hidden '_method' field is 'PUT'
        method = request.form.get('_method', request.method).upper()
        # check form method 
        if method == 'PUT':
            note = Note.query.get_or_404(request.form.get('note_id'))
            # check owner
            if note.author != current_user:
                abort(403)
            
            note.title = form.title.data
            note.content = form.content.data
            db.session.commit()
        else:
            note = Note(
                title=form.title.data,
                content=form.content.data,
                user_id=current_user.id
            )
            db.session.add(note)
            db.session.commit()
            
        flash('Note saved successfully', 'success')
        return redirect(url_for('notes.dashboard', note_id=note.id, task='edit'))
    else:
        flash('Failed to save note', 'danger')
        return redirect(url_for('notes.dashboard', task='new'))
    

@notes_bp.route('/delete/<int:note_id>', methods=['POST', 'DELETE'])
@login_required
def delete(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)
    
    note.deleted_at = datetime.now(timezone.utc)
    db.session.commit()
    flash('Note deleted successfully', 'success')
    return redirect(url_for('notes.dashboard'))

@notes_bp.route('/pin/<int:note_id>', methods=['POST'])
@login_required
def pin(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)

    note.is_pinned = not note.is_pinned
    db.session.commit()
    
    status = "pinned" if note.is_pinned else "unpinned"
    flash(f'Note {status} successfully', 'success')
    return redirect(url_for('notes.dashboard', note_id=note.id, task=request.args.get('task', 'preview')))

@notes_bp.route('/export/<int:note_id>')
@login_required
def export(note_id):
    note = Note.query.get_or_404(note_id)
    if note.author != current_user:
        abort(403)

    return Response(
        _note_markdown(note),
        mimetype='text/markdown',
        headers={
            'Content-Disposition': f'attachment; filename="{_note_filename(note)}"'
        }
    )

@notes_bp.route('/export-all')
@login_required
def export_all():
    notes = Note.query.filter_by(user_id=current_user.id).filter(Note.deleted_at.is_(None)).order_by(Note.title).all()

    if not notes:
        flash('You have no notes to export', 'danger')
        return redirect(url_for('notes.dashboard'))

    buffer = io.BytesIO()
    used_names = set()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for note in notes:
            filename = _note_filename(note)
            # Guard against unlikely filename collisions within the archive
            while filename in used_names:
                filename = f"{filename.rsplit('.', 1)[0]}-copy.md"
            used_names.add(filename)
            zf.writestr(filename, _note_markdown(note))
    buffer.seek(0)

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d')
    return Response(
        buffer.getvalue(),
        mimetype='application/zip',
        headers={
            'Content-Disposition': f'attachment; filename="notes-export-{timestamp}.zip"'
        }
    )