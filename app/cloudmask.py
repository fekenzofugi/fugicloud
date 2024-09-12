from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db
import os

bp = Blueprint('cloudmask', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, img, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('cloudmask/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        img = request.form['img']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, img, author_id)'
                ' VALUES (?, ?, ?, ?)',
                (title, body, img, g.user['id'])
            )
            db.commit()
            return redirect(url_for('cloudmask.index'))

    return render_template('cloudmask/create.html', data=["sen2cor", "fmask", "s2cloudless"])


@bp.route('/create', methods=['POST'])
@login_required
def upload_file():
    # Check if the POST request has the file part
    if 'img' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['img']

    # If user does not select a file, the browser submits an empty part without filename
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Secure the filename and save it to the target folder
    file_path = os.path.join("app/static/uploads", file.filename)
    file.save(file_path)

    return jsonify({'message': 'File uploaded successfully', 'file_path': file_path})


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, img, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        img = request.form['img']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?, img = ?'
                ' WHERE id = ?',
                (title, body, img, id)
            )
            db.commit()
            return redirect(url_for('cloudmask.index'))

    return render_template('cloudmask/update.html', post=post, data=["sen2cor", "fmask", "s2cloudless"])

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('cloudmask.index'))