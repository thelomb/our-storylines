from flask import (render_template, flash, redirect, url_for, request,
                   current_app, jsonify, Markup)
from application import db
from application.main import bp
from application.main.forms import (EditProfileForm,
                                    PostForm, ItineraryForm, FullStoryForm)
from flask_login import current_user, login_required
from application.models import (User, Story, Media,
                                Tag, Itinerary)
from datetime import date, datetime
from random import randint
from flask_googlemaps import Map
from googlemaps import Client
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
                                 odometer_at=form.odometer_read.data,
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
                         odometer_at=form.odometer_read.data,
                         travel_type=form.travel_type.data,
                         stay_type=form.stay_type.data,
                         author=current_user,
                         files=request.files.getlist('post_images')
                         )
        flash('Your story is now published')
        return redirect(url_for('main.index'))
    elif request.method == 'GET':
        form.day.data = fullstory.date_for
        form.title.data = fullstory.title
        form.post.data = fullstory.content
        form.stay.data = fullstory.stay_place
        form.start.data = fullstory.start_place
        form.end.data = fullstory.end_place
        form.odometer_read.data = fullstory.odometer_at
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


def simulate_media():
    media = ([Media(name=\
                              'https://picsum.photos/700/300/?gravity=east&image=' \
                              + str(randint(1,90)),
                              filename='https://picsum.photos/700/300/?gravity=east&image=' + str(randint(1,90)),
                              url='https://picsum.photos/700/300/?gravity=east&image=' + str(randint(1,90)),
                              type='Image') for _ in range(3)])
    return media


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
    image = Media.query.get(picture_id)
    db.session.delete(image)
    db.session.commit()
    return redirect(url_for('main.edit_story', story_id=story_id))


@bp.route('/new_itinerary', methods=['GET', 'POST'])
@login_required
def new_itinerary():
    form = ItineraryForm()
    print(request.form)
    if form.validate_on_submit():
        itinerary = Itinerary(
            planning_description=form.planning_description.data,
            day=form.day.data,
            planned_start_point=form.planned_start_point.data,
            planned_end_point=form.planned_end_point.data,
            planned_distance=form.planned_distance.data,
            planned_stay=form.planned_stay.data
        )
        db.session.add(itinerary)
        db.session.commit()
        flash('Itinéraire créé!')
        return redirect(url_for('main.index'))
    return render_template('itinerary.html', form=form)


@bp.route('/itinerary/edit_<int:itinerary_id>', methods=['GET', 'POST'])
@login_required
def edit_itinerary(itinerary_id):
    form = ItineraryForm()
    itinerary = Itinerary.query.get(itinerary_id)
    if form.validate_on_submit():
        itinerary = Itinerary(
            planning_description=form.planning_description.data,
            day=form.day.data,
            planned_start_point=form.planned_start_point.data,
            planned_end_point=form.planned_end_point.data,
            planned_distance=form.planned_distance.data,
            planned_stay=form.planned_stay.data
        )
        db.session.add(itinerary)
        db.session.commit()
        flash('Your story is now updated')
        return redirect(url_for('main.index'))
    elif request.method == 'GET':
        form.planning_description.data = itinerary.planning_description
        form.day.data = itinerary.day
        form.planned_start_point.data = itinerary.planned_start_point
        form.planned_end_point.data = itinerary.planned_end_point
        form.planned_distance.data = itinerary.planned_distance
        form.planned_stay.data = itinerary.planned_stay
        return render_template('itinerary.html',
                               title="What's new?",
                               form=form,
                               itinerary=itinerary,
                               )


@bp.route('/itinerary/<int:page>')
@login_required
def itinerary(page=1):
    itineraries = Itinerary.query.order_by(Itinerary.day.asc()).paginate(
        page, current_app.config['ITINERARIES_PER_PAGE'], False)
    return render_template('itineraries.html', title='Home',
                           itineraries=itineraries.items, page=page)


@bp.route('/story_date/<a_date>', methods=['GET'])
@login_required
def view_story_date1(a_date):
    # story = Story.query.get(story_id)
    entry = {}
    entry['date'] = date(2019, 5, 24)
    entry['title'] = 'A Journey Through Utah'
    entry['html_content'] = '''
    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
    '''
    entry['media'] = ['https://picsum.photos/700/300/?gravity=east&image=' + str(randint(1,90)) for _ in range(3)]
    entry['id'] = 1
    entry['from'] = 'LA'
    entry['to'] = 'Joshua National Park'
    mymap = Map(
        identifier="view-side",
        lat=37.4419,
        lng=-122.1419,
        markers=[(37.4419, -122.1419)]
    )
    geolocation = Client(current_app.config['GOOGLEMAPS_KEY'])
    geocode_result = geolocation.geocode('''LA''')
    lat = geocode_result[0]['geometry']['location']['lat']
    lng = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''SF''')
    lat2 = geocode_result[0]['geometry']['location']['lat']
    lng2 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''San Jose, CA''')
    lat3 = geocode_result[0]['geometry']['location']['lat']
    lng3 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Salinas, CA''')
    lat4 = geocode_result[0]['geometry']['location']['lat']
    lng4 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Fresno, CA''')
    lat5 = geocode_result[0]['geometry']['location']['lat']
    lng5 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Santa Maria, CA''')
    lat6 = geocode_result[0]['geometry']['location']['lat']
    lng6 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Santa Barbara, CA''')
    lat7 = geocode_result[0]['geometry']['location']['lat']
    lng7 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Death Valley National Park''')
    lat8 = geocode_result[0]['geometry']['location']['lat']
    lng8 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Sequoia National Forest''')
    lat9 = geocode_result[0]['geometry']['location']['lat']
    lng9 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Visalia, CA''')
    lat10 = geocode_result[0]['geometry']['location']['lat']
    lng10 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Yosemite National Park''')
    lat11 = geocode_result[0]['geometry']['location']['lat']
    lng11 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Bakersfield, CA''')
    lat12 = geocode_result[0]['geometry']['location']['lat']
    lng12 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Riverside, CA''')
    lat13 = geocode_result[0]['geometry']['location']['lat']
    lng13 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Lost Hills, CA''')
    lat14 = geocode_result[0]['geometry']['location']['lat']
    lng14 = geocode_result[0]['geometry']['location']['lng']
    sndmap = Map(
        identifier="sndmap",
        style="width:100%;height:100%;margin:0;",
        # lat=37.4419,
        # lng=-122.1419,
        lat=lat,
        lng=lng,
        fit_markers_to_bounds=True,
        markers=[
          {
             'icon': Markup('http://localhost:5000/static/images/ic_place_24px.svg'),
             'lat': lat,
             'lng': lng,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
             'lat': lat2,
             'lng': lng2,
             'infobox': "<b>Hello World from other place</b>",
             'title':'finish'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-add_circle-24px.svg'),
             'lat': lat3,
             'lng': lng3,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-beach_access-24px.svg'),
             'lat': lat4,
             'lng': lng4,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-commute-24px.svg'),
             'lat': lat5,
             'lng': lng5,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/twotone-room-24px.svg'),
             'lat': lat6,
             'lng': lng6,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/twotone-room-arrival.svg'),
             'lat': lat7,
             'lng': lng7,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-flight-24px.svg'),
             'lat': lat8,
             'lng': lng8,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-flight_land-24px.svg'),
             'lat': lat9,
             'lng': lng9,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-flight_takeoff-24px.svg'),
             'lat': lat10,
             'lng': lng10,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-hotel-24px.svg'),
             'lat': lat11,
             'lng': lng11,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/twotone-flag-24px.svg'),
             'lat': lat12,
             'lng': lng12,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-room-24px.svg'),
             'lat': lat13,
             'lng': lng13,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-style-24px.svg'),
             'lat': lat14,
             'lng': lng14,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          }
        ]
    )
    if geocode_result:
        print(geocode_result[0]['geometry']['location'])
    else:
        print('No match')
    return render_template('view_story_date.html',
                           story=entry, map1=mymap, map2=sndmap)


@bp.route('/story_date_sandbox', methods=['GET'])
@login_required
def story_date_sandbox():
    # story = Story.query.get(story_id)
    entry = {}
    entry['date'] = date(2019, 5, 24)
    entry['title'] = 'A Journey Through Utah'
    entry['html_content'] = '''
    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
    '''
    entry['media'] = ['https://picsum.photos/700/300/?gravity=east&image=' + str(randint(1,90)) for _ in range(3)]
    entry['id'] = 1
    entry['from'] = 'LA'
    entry['to'] = 'Joshua National Park'
    mymap = Map(
        identifier="view-side",
        lat=37.4419,
        lng=-122.1419,
        markers=[(37.4419, -122.1419)]
    )
    geolocation = Client(current_app.config['GOOGLEMAPS_KEY'])
    geocode_result = geolocation.geocode('''LA''')
    lat = geocode_result[0]['geometry']['location']['lat']
    lng = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''SF''')
    lat2 = geocode_result[0]['geometry']['location']['lat']
    lng2 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''San Jose, CA''')
    lat3 = geocode_result[0]['geometry']['location']['lat']
    lng3 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Salinas, CA''')
    lat4 = geocode_result[0]['geometry']['location']['lat']
    lng4 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Fresno, CA''')
    lat5 = geocode_result[0]['geometry']['location']['lat']
    lng5 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Santa Maria, CA''')
    lat6 = geocode_result[0]['geometry']['location']['lat']
    lng6 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Santa Barbara, CA''')
    lat7 = geocode_result[0]['geometry']['location']['lat']
    lng7 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Death Valley National Park''')
    lat8 = geocode_result[0]['geometry']['location']['lat']
    lng8 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Sequoia National Forest''')
    lat9 = geocode_result[0]['geometry']['location']['lat']
    lng9 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Visalia, CA''')
    lat10 = geocode_result[0]['geometry']['location']['lat']
    lng10 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Yosemite National Park''')
    lat11 = geocode_result[0]['geometry']['location']['lat']
    lng11 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Bakersfield, CA''')
    lat12 = geocode_result[0]['geometry']['location']['lat']
    lng12 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Riverside, CA''')
    lat13 = geocode_result[0]['geometry']['location']['lat']
    lng13 = geocode_result[0]['geometry']['location']['lng']
    geocode_result = geolocation.geocode('''Lost Hills, CA''')
    lat14 = geocode_result[0]['geometry']['location']['lat']
    lng14 = geocode_result[0]['geometry']['location']['lng']
    sndmap = Map(
        identifier="sndmap",
        style="width:100%;height:100%;margin:0;",
        # lat=37.4419,
        # lng=-122.1419,
        lat=lat,
        lng=lng,
        fit_markers_to_bounds=True,
        markers=[
          {
             'icon': Markup('http://localhost:5000/static/images/ic_place_24px.svg'),
             'lat': lat,
             'lng': lng,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
             'lat': lat2,
             'lng': lng2,
             'infobox': "<b>Hello World from other place</b>",
             'title':'finish'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-add_circle-24px.svg'),
             'lat': lat3,
             'lng': lng3,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-beach_access-24px.svg'),
             'lat': lat4,
             'lng': lng4,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-commute-24px.svg'),
             'lat': lat5,
             'lng': lng5,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/twotone-room-24px.svg'),
             'lat': lat6,
             'lng': lng6,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/twotone-room-arrival.svg'),
             'lat': lat7,
             'lng': lng7,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-flight-24px.svg'),
             'lat': lat8,
             'lng': lng8,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-flight_land-24px.svg'),
             'lat': lat9,
             'lng': lng9,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-flight_takeoff-24px.svg'),
             'lat': lat10,
             'lng': lng10,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-hotel-24px.svg'),
             'lat': lat11,
             'lng': lng11,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/twotone-flag-24px.svg'),
             'lat': lat12,
             'lng': lng12,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-room-24px.svg'),
             'lat': lat13,
             'lng': lng13,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          },
          {
             'icon': Markup('http://localhost:5000/static/images/baseline-style-24px.svg'),
             'lat': lat14,
             'lng': lng14,
             'infobox': "<b>Hello World</b>",
             'id': 'start'
          }
        ]
    )
    if geocode_result:
        print(geocode_result[0]['geometry']['location'])
    else:
        print('No match')
    return render_template('view_story_date_sandbox.html',
                           story=entry, map1=mymap, map2=sndmap)


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
