from flask import (render_template, flash, redirect, url_for, request,
                   current_app)
from application import db
from application.main import bp
from application.main.forms import (EditProfileForm,
                                    PostForm)
from flask_login import current_user, login_required
from application.models import User, Story, Storyline
from datetime import datetime
from application import images


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        filename = None
        url = None
        if request.files:
            if request.files['post_images']:
                filename = images.save(request.files['post_images'])
                url = images.url(filename)
        print(f"filename is: {filename}")
        story = Story(content=form.post.data, author=current_user,
                      image_filename=filename, image_url=url)
        db.session.add(story)
        db.session.commit()
        flash('Your story is now published')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    stories = current_user.stories.order_by(Story.timestamp.desc()).paginate(
        page, current_app.config['STORIES_PER_PAGE'], False)
    next_url = url_for('main.index', page=stories.next_num) \
        if stories.has_next else None
    prev_url = url_for('main.index', page=stories.prev_num) \
        if stories.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           posts=stories.items, next_url=next_url,
                           prev_url=prev_url, pages=stories.pages)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    stories = user.stories.order_by(Story.timestamp.desc()).paginate(
        page, current_app.config['STORIES_PER_PAGE'], False)
    next_url = url_for('main.user', username=user.username,
                       page=stories.next_num) \
        if stories.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=stories.prev_num) \
        if stories.has_prev else None
    return render_template('user.html', user=user, posts=stories.items,
                           next_url=next_url, prev_url=prev_url)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',
                           title='Edit Profile', form=form)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    stories = Story.query.order_by(Story.timestamp.desc()).paginate(
        page, current_app.config['STORIES_PER_PAGE'], False)
    next_url = url_for('main.explore', page=stories.next_num) \
        if stories.has_next else None
    prev_url = url_for('main.explore', page=stories.prev_num) \
        if stories.has_prev else None
    return render_template('index.html', title='Explore',
                           posts=stories.items,
                           next_url=next_url, prev_url=prev_url,
                           pages=stories.pages)
