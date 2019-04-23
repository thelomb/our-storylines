from flask import (render_template,
                   flash,
                   redirect,
                   url_for,
                   request,
                   current_app)
from application import db
from application.main import bp
from application.main.forms import (EditProfileForm,
                                    FullStoryForm,
                                    CommentForm)
from flask_login import current_user, login_required
from application.models import (User,
                                Story,
                                Media,
                                Storyline,
                                StorylineMembership)
from datetime import date, datetime
from application.fullstory_service import Fullstory2
from application.location_service import map_a_story
from wtforms import TextField, SelectField
from application.helpers import authorized_storyline
from application.model_enums import ImageFeature

stay_type_icons = {
    'CAMPING': 'fa-campground',
    'HOTEL': 'fa-hotel',
    'FRIENDS': 'fa-home',
    'HOUSE': 'fa-umbrella-beach'

}


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/')
@bp.route('/<storyline>')
@bp.route('/<storyline>/<int:page>')
@login_required
@authorized_storyline
def index(storyline=None, page=1):
    if not storyline:
        sl = current_user.current_storyline()
        if sl is None:
            return render_template('errors/404.html')
    else:
        sl = Storyline.query.filter_by(slug=storyline).first_or_404()
    media = sl.pictures()
    paginated_stories = sl.stories.order_by(Story.date_for.desc()).paginate(
        page, current_app.config['STORIES_PER_PAGE'], False)

    return render_template('index.html',
                           title='Home',
                           posts=paginated_stories.items,
                           page=page,
                           storyline=sl,
                           media=media)


@bp.route('/<storyline>/new', methods=['GET', 'POST'])
@login_required
@authorized_storyline
def fullstory(storyline):
    sl = Storyline.query.filter_by(slug=storyline).first_or_404()
    form = FullStoryForm()
    if form.validate_on_submit():
        Fullstory2.from_web_form(date_for=form.day.data,
                                 title=form.title.data,
                                 content=form.post.data,
                                 start_place=form.start.data,
                                 end_place=form.end.data,
                                 stay_place=form.stay.data,
                                 odometer_at=str_to_int(
                                     form.odometer_read.data),
                                 travel_type=form.travel_type.data,
                                 stay_type=form.stay_type.data,
                                 author=current_user,
                                 files=request.files.getlist('post_images'),
                                 storyline=sl,
                                 stay_description=form.stay_description.data
                                 )
        # flash('Vous venez de publier une nouvelle journée!', 'info')
        return redirect(url_for('main.view_story_date',
                                storyline=sl.slug,
                                a_date=form.day.data.
                                strftime('%d-%m-%Y')))
    elif request.method == 'GET':
        form.day.data = date.today()
    return render_template('new_story.html',
                           form=form,
                           storyline=sl)


@bp.route('/<storyline>/<a_date>', methods=['GET', 'POST'])
@login_required
@authorized_storyline
def view_story_date(storyline, a_date):
    print(request.headers)
    form = CommentForm()
    sl = Storyline.query.filter_by(slug=storyline).first_or_404()
    try:
        story_date_parameter = a_date.split("-")
        story_date = date(int(story_date_parameter[2]),
                          int(story_date_parameter[1]),
                          int(story_date_parameter[0]))
        story = Fullstory2.get_by_date_web(date_for=story_date,
                                           storyline=storyline)
        if story is None:
            raise ValueError
    except (ValueError, IndexError, AttributeError):
        return render_template('errors/404.html')

    story.media = story.media.order_by(Media.image_ratio)
    sndmap = map_a_story(story)
    if form.validate_on_submit():
        story.add_comment(comment=form.comment.data,
                          author=current_user)
        form.comment.data = None
    inline_image(story)
    return render_template('view_story_date.html',
                           story=story,
                           map2=sndmap,
                           prev_story_date=story.prev_date,
                           next_story_date=story.next_date,
                           title=story.title,
                           stay_type_icons=stay_type_icons,
                           storyline=sl,
                           form=form)


@bp.route('/<storyline>/edit_story/<a_date>', methods=['GET', 'POST'])
@login_required
@authorized_storyline
def edit_story_date1(storyline, a_date):
    class FullStoryFormWithComments(FullStoryForm):
        pass

        def validate(self):
            featuredFields = {}
            for name, value in self.data.items():
                if (name.startswith('feature') and
                        value != ImageFeature.NONE.name):
                    featuredFields[value] = \
                        featuredFields.get(value, 0) + 1

            for feature, nbitem in featuredFields.items():
                if nbitem > 1:
                    self.post_images.errors = ["problème d'image"]
                    return False
            return True

    sl = Storyline.query.filter_by(slug=storyline).first_or_404()

    try:
        story_date_parameter = a_date.split("-")
        story_date = date(int(story_date_parameter[2]),
                          int(story_date_parameter[1]),
                          int(story_date_parameter[0]))
        fullstory = Fullstory2.get_by_date_web(date_for=story_date,
                                               storyline=storyline)
        if fullstory is None:
            raise ValueError
    except (ValueError, IndexError, AttributeError):
        return render_template('errors/404.html')
    if fullstory.story.media:
        for medium in fullstory.story.media:
            setattr(FullStoryFormWithComments,
                    medium.filename + 'comment',
                    TextField('', render_kw={'placeholder':
                                             'Commentez cette photo'}))
            setattr(FullStoryFormWithComments,
                    'feature' + medium.filename,
                    SelectField("Action spéciale",
                                choices=ImageFeature.choices()))
    form = FullStoryFormWithComments()
    if form.validate_on_submit():
        image_addons = get_image_addons(form=form,
                                        media=fullstory.story.media)
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
                         files=request.files.getlist('post_images'),
                         image_addons=image_addons,
                         stay_description=form.stay_description.data
                         )
        # flash("L'entrée vient d'être mise à jour", 'info')
        return redirect(url_for('main.view_story_date',
                                storyline=sl.slug,
                                a_date=fullstory.date_for.
                                strftime('%d-%m-%Y')))
    elif request.method == 'GET':
        form.id.data = fullstory.story.id
        form.day.data = fullstory.date_for
        form.title.data = fullstory.title
        form.post.data = fullstory.content
        form.stay.data = fullstory.stay_place
        form.start.data = fullstory.start_place
        form.end.data = fullstory.end_place
        form.odometer_read.data = int_to_str(fullstory.odometer_at)
        form.travel_type.data = fullstory.travel_type
        form.stay_type.data = fullstory.stay_type
        form.stay_description.data = fullstory.stay_description
        if fullstory.story.media:
            for medium in fullstory.story.media:
                form[medium.filename + 'comment'].data = medium.comment
                form['feature' + medium.filename].data = medium.feature.name
    return render_template('new_story.html',
                           form=form,
                           story=fullstory.story,
                           storyline=sl)


@bp.route('/<storyline>/community')
@login_required
@authorized_storyline
def storyline_community(storyline):
    sl = Storyline.query.filter_by(slug=storyline).first_or_404()
    memberships = sl.members.join(StorylineMembership.member).\
        order_by(User.last_seen.desc()).\
        all()
    return render_template('community.html',
                           current_user=current_user,
                           memberships=memberships,
                           storyline=sl,
                           title='Boulomb & Friends'
                           # posts=stories.items,
                           # next_url=next_url,
                           # prev_url=prev_url
                           )


@bp.route('/edit_profile/<username>', methods=['GET', 'POST'])
@login_required
def edit_profile(username):
    if current_user.username == username:
        user = User.query.filter_by(username=username).first_or_404()
        form = EditProfileForm(current_user.username)
        if form.validate_on_submit():
            file = request.files.getlist('picture')
            user.update(username=form.username.data,
                        about_me=form.about_me.data,
                        file=file)
            user.save()

            return redirect(url_for('main.storyline_community',
                                    storyline=user.
                                    current_storyline().slug))
        elif request.method == 'GET':
            form.username.data = user.username
            form.about_me.data = user.about_me
        return render_template('edit_profile.html',
                               title='Edit Profile',
                               form=form,
                               storyline=user.
                               current_storyline(),
                               user=user)
    else:
        return render_template('errors/404.html')


@bp.route('/<storyline>/<a_date>/delete_picture/<int:picture_id>')
@login_required
@authorized_storyline
def delete_picture(storyline, a_date, picture_id):
    try:
        story_date_parameter = a_date.split("-")
        story_date = date(int(story_date_parameter[2]),
                          int(story_date_parameter[1]),
                          int(story_date_parameter[0]))
        fullstory = Fullstory2.get_by_date_web(date_for=story_date,
                                               storyline=storyline)
        if fullstory is None:
            raise ValueError
    except (ValueError, IndexError, AttributeError):
        return render_template('errors/404.html')

    image = fullstory.media.filter_by(id=picture_id).first()
    if image:
        db.session.delete(image)
        db.session.commit()
    return redirect(url_for('main.edit_story_date1',
                            storyline=storyline,
                            a_date=a_date))


def get_image_addons(form, media):
    add_ons = {}
    comments = {}
    features = {}
    for medium in media:
        comments[medium.filename] = form[medium.filename + 'comment'].data
        features[medium.filename] = form['feature' + medium.filename].data
        print(form['feature' + medium.filename].data)
    add_ons['comments'] = comments
    add_ons['features'] = features
    return add_ons


# def simulate_media():
#     picsum = 'https://picsum.photos/700/300/?gravity=east&image='
#     media = ([Media(name=picsum +
#                     str(randint(1, 90)),
#                     filename=picsum + str(randint(1, 90)),
#                     url=picsum + str(randint(1, 90)),
#                     type='Image',
#                     request_file_name=None,
#                     location=None,
#                     exif_width=1,
#                     exif_height=1) for _ in range(3)])
#     return media


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


def inline_image(story):
    if story.html_content:
        paragraph_end = '</p>'
        position = 0
        content = story.html_content
        for i, f in enumerate(ImageFeature):
            if not (f == ImageFeature.NONE or
                    f == ImageFeature.FEATURED):
                position += 1
                if position % 2 == 0:
                    float = 'left mr-2'
                else:
                    float = 'right ml-2'
                image = story.featured_image(f)
                if image:
                    insert = ('</p><img src="' +
                              image.url +
                              '" class="inline-img float-' +
                              float +
                              '"alt="' +
                              image.name +
                              '">')
                    content = nth_repl(content,
                                       paragraph_end,
                                       insert,
                                       position)
        story.html_content = content


def nth_repl(s, sub, repl, nth):
    find = s.find(sub)
    # if find is not p1 we have found at least one match for the substring
    i = find != -1
    # loop util we find the nth or we find no match
    while find != -1 and i != nth:
        # find + 1 means we start at the last match start index + 1
        find = s.find(sub, find + 1)
        if find != -1:
            i += 1
    # if i  is equal to nth we found nth matches so replace
    if i == nth:
        return s[:find] + repl + s[find + len(sub):]
    return s


def excerpt(text, story, end_tag=None):
    if end_tag is None:
        end_tag = '<a href="">...</a>'
    return text[:100] + end_tag
