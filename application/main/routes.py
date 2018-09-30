from flask import (render_template, flash, redirect, url_for, request,
                   current_app, jsonify)
from application import db
from application.main import bp
from application.main.forms import (EditProfileForm,
                                    PostForm)
from flask_login import current_user, login_required
from application.models import User, Story, Storyline, Media, Tag, Itinerary
from datetime import datetime
from application import images
from sqlalchemy import update


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/')
@bp.route('/index/<int:page>')
@login_required
def index(page=1):
    stories = current_user.stories.order_by(Story.timestamp.desc()).paginate(
        page, current_app.config['STORIES_PER_PAGE'], False)
    return render_template('index.html', title='Home',
                           posts=stories.items, page=page)


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


def media_request(media_request):
        photos = []
        # audios = []
        # videos = []
        media = {
            'photo': [],
            # 'video': [],
            # 'audio': []
        }
        if media_request:
            for image in media_request.getlist('post_images'):
                filename = images.save(image)
                url = images.url(filename)
                photos.append({'filename': filename, 'url': url})
                media['photo'] = photos
        return media


def tag_request(tag_request):
    post_tags = []
    if tag_request:
        existing_tags = [name for name, in Tag.query.with_entities(
            Tag.name)]
        form_tags = tag_request.split(', ')
        for tag in form_tags:
            if tag not in existing_tags:
                t = Tag(name=tag)
                db.session.add(t)
                post_tags.append(t)
            else:
                post_tags.append(Tag.query.filter(Tag.name == tag).first())
    return post_tags


@bp.route('/story', methods=['GET', 'POST'])
@login_required
def story():
    form = PostForm()
    if form.validate_on_submit():
        media = media_request(request.files)
        tags = tag_request(request.form['tags'])

        story = Story(title=form.title.data, content=form.post.data,
                      author=current_user, tags=tags)
        for medium in media['photo']:
            img = Media(type='Image', name=medium['filename'],
                        filename=medium['filename'], url=medium['url'],
                        related_story=story)
            db.session.add(img)

        db.session.add(story)
        db.session.commit()
        flash('Your story is now published')
        return redirect(url_for('main.index'))
    return render_template('story.html', form=form)


@bp.route('/story/<int:story_id>', methods=['GET'])
@login_required
def view_story(story_id):
    story = Story.query.get(story_id)
    return render_template('view_story.html',
                           title="What's new?",
                           story=story)


@bp.route('/story/edit_<int:story_id>', methods=['GET', 'POST'])
@login_required
def edit_story(story_id):
    form = PostForm()
    story = Story.query.get(story_id)
    if form.validate_on_submit():
        story.title = form.title.data
        story.content = form.post.data
        story.author = current_user
        story.tags = tag_request(request.form['tags'])
        media = media_request(request.files)
        for medium in media['photo']:
            img = Media(type='Image', name=medium['filename'],
                        filename=medium['filename'], url=medium['url'],
                        related_story=story)
            db.session.add(img)

        db.session.add(story)
        db.session.commit()
        flash('Your story is now updated')
        return redirect(url_for('main.index'))
    elif request.method == 'GET':
        form.title.data = story.title
        form.post.data = story.html_content
        tag_placeholders = ', '.join([t.name for t in story.tags])
        return render_template('story.html',
                               title="What's new?",
                               form=form,
                               story=story,
                               tags=tag_placeholders)


@bp.route('/story/<int:story_id>/delete_picture/<int:picture_id>')
@login_required
def delete_picture(story_id, picture_id):
    print(picture_id)
    image = Media.query.get(picture_id)
    db.session.delete(image)
    db.session.commit()
    return redirect(url_for('main.edit_story', story_id=story_id))
