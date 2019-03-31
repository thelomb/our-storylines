from flask import (render_template,
                   flash,
                   redirect,
                   url_for,
                   request,
                   current_app)
from application import db
from application.main import bp
from application.main.forms import (EditProfileForm,
                                    FullStoryForm)
from flask_login import current_user, login_required
from application.models import (User,
                                Story,
                                Media)
from datetime import date, datetime
from random import randint
from application.fullstory_service import Fullstory2
from application.location_service import map_a_story


stay_type_icons = {
    'CAMPING': 'fa-campground',
    'HOTEL': 'fa-hotel',
    'FRIENDS': 'fa-smile-beam',
    'HOUSE': 'fa-umbrella-beach'

}


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/')
@bp.route('/index/<int:page>')
@login_required
def index(page=1):
    stories = Story.query.order_by(Story.date_for.desc()).paginate(
        page, current_app.config['STORIES_PER_PAGE'], False)
    return render_template('index.html', title='Home',
                           posts=stories.items, page=page)


@bp.route('/fullstory', methods=['GET', 'POST'])
@login_required
def fullstory():
    form = FullStoryForm()
    if form.validate_on_submit():
        Fullstory2.from_web_form(date_for=form.day.data,
                                 title=form.title.data,
                                 content=form.post.data,
                                 start_place=form.start.data,
                                 end_place=form.end.data,
                                 stay_place=form.stay.data,
                                 odometer_at=str_to_int(form.odometer_read.data),
                                 travel_type=form.travel_type.data,
                                 stay_type=form.stay_type.data,
                                 author=current_user,
                                 files=request.files.getlist('post_images')
                                 )
        flash('Your story is now published')
        return redirect(url_for('main.index'))
    elif request.method == 'GET':
        form.day.data = date.today()
    return render_template('fullstory.html', form=form)


@bp.route('/story_date/<a_date>', methods=['GET'])
@login_required
def view_story_date(a_date):
    story_date_parameter = a_date.split("-")
    story_date = date(int(story_date_parameter[2]),
                      int(story_date_parameter[1]),
                      int(story_date_parameter[0]))
    print('getting story')
    story = Fullstory2.get_by_date_web(date_for=story_date)
    if story is None:
        return render_template('errors/404.html')
    if story.media.count() == 0:
        story.media = simulate_media()
    sndmap = map_a_story(story)
    return render_template('view_story_date.html',
                           story=story,
                           map2=sndmap,
                           prev_story_date=story.prev_date,
                           next_story_date=story.next_date,
                           title=story.title,
                           stay_type_icons=stay_type_icons)


@bp.route('/edit_story_date/<a_date>', methods=['GET', 'POST'])
@login_required
def edit_story_date1(a_date):
    # story = Story.query.get(story_id)
    story_date_parameter = a_date.split("-")
    story_date = date(int(story_date_parameter[2]),
                      int(story_date_parameter[1]),
                      int(story_date_parameter[0]))
    fullstory = Fullstory2.get_by_date_web(date_for=story_date)
    form = FullStoryForm()
    if form.validate_on_submit():
        fullstory.update(date_for=form.day.data,
                         title=form.title.data,
                         content=form.post.data,
                         start_place=form.start.data,
                         end_place=form.end.data,
                         stay_place=form.stay.data,
                         odometer_at=str_to_int(form.odometer_read.data),
                         travel_type=form.travel_type.data,
                         stay_type=form.stay_type.data,
                         author=current_user,
                         files=request.files.getlist('post_images')
                         )
        flash("L'entrée vient d'être mise à jour", 'info')
        return redirect(url_for('main.view_story_date',
                                a_date=fullstory.date_for.
                                strftime('%d-%m-%Y')))
    elif request.method == 'GET':
        form.day.data = fullstory.date_for
        form.title.data = fullstory.title
        form.post.data = fullstory.content
        form.stay.data = fullstory.stay_place
        form.start.data = fullstory.start_place
        form.end.data = fullstory.end_place
        print('in get, fullstory.end_place', fullstory.end_place)
        form.odometer_read.data = int_to_str(fullstory.odometer_at)
        form.travel_type.data = fullstory.travel_type
        form.stay_type.data = fullstory.stay_type
    return render_template('fullstory.html', form=form, story=fullstory.story)


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
        current_user.update(**form.data)  # save the object with changes
        flash('Your changes have been saved')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',
                           title='Edit Profile', form=form)


def str_to_int(string):
    try:
        int(float(string))
        return int(float(string))
    except ValueError:
        return None


def int_to_str(int):
    if int:
        return str(int)
    return ''


def simulate_media():
    media = ([Media(name=\
                              'https://picsum.photos/700/300/?gravity=east&image=' \
                              + str(randint(1,90)),
                              filename='https://picsum.photos/700/300/?gravity=east&image=' + str(randint(1,90)),
                              url='https://picsum.photos/700/300/?gravity=east&image=' + str(randint(1,90)),
                              type='Image') for _ in range(3)])
    return media


@bp.route('/story/<int:story_id>/delete_picture/<int:picture_id>')
@login_required
def delete_picture(story_id, picture_id):
    image = Media.query.get(picture_id)
    db.session.delete(image)
    db.session.commit()
    return redirect(url_for('main.edit_story', story_id=story_id))


# def tag_request(tag_request):
#     post_tags = []
#     if tag_request:
#         existing_tags = [name for name, in Tag.query.with_entities(
#             Tag.name)]
#         form_tags = tag_request.split(', ')
#         for tag in form_tags:
#             if tag not in existing_tags:
#                 t = Tag(name=tag)
#                 db.session.add(t)
#                 post_tags.append(t)
#             else:
#                 post_tags.append(Tag.query.filter(Tag.name == tag).first())
#     return post_tags
