from httpobs.website import add_response_headers
from flask import Blueprint, jsonify, request
import httpobs.database as database
from googleplaces import GooglePlaces
from str2bool import str2bool

api = Blueprint('api', __name__)

# TODO: Implement API to write public and private headers to the database
@api.route('/api/v1/register', methods=['POST', 'GET'])
@add_response_headers(cors=True)
def api_register():
    email = request.args.get('email')
    password = request.args.get('password')
    super_admin = None
    client_admin = None
    agency_user = None
    client_id = None
    if request.args.get('super_admin'):
        super_admin = str2bool(request.args.get('super_admin'))
    if request.args.get('client_admin'):
        client_admin = str2bool(request.args.get('client_admin'))
    if request.args.get('agency_user'):
        agency_user = str2bool(request.args.get('agency_user'))
    if request.args.get('client_id'):
        client_id = request.args.get('client_id')

    auth_info = {'email': email, 'password': password, 'super_admin': super_admin,
                 'client_admin': client_admin, 'agency_user': agency_user, 'client_id': client_id
                 }
    return jsonify(database.select_register(auth_info=auth_info))

@api.route('/api/v1/login', methods=['POST', 'GET'])
@add_response_headers(cors=True)
def api_login():
    email = request.args.get('email')
    password = request.args.get('password')

    login_info = {'email': email, 'password': password}
    return jsonify(database.select_login(login_info=login_info))

@api.route('/api/v1/logout', methods=['POST', 'GET'])
@add_response_headers(cors=True)
def api_logout():
    return jsonify(database.select_logout())

@api.route('/api/v1/user_edit', methods=['POST', 'GET'])
@add_response_headers(cors=True)
def api_user_edit():
    email = request.args.get('email')
    password = request.args.get('password')
    user_id = request.args.get('user_id')
    client_admin = None
    agency_user = None
    client_id = None
    if request.args.get('client_admin'):
        client_admin = str2bool(request.args.get('client_admin'))
    if request.args.get('agency_user'):
        agency_user = str2bool(request.args.get('agency_user'))
    if request.args.get('client_id'):
        if request.args.get('client_id') == 'null':
            client_id = str2bool(request.args.get('client_id'))
        else:
            client_id = request.args.get('client_id')

    auth_info = {'email': email, 'password': password,
                 'user_id': user_id, 'client_admin': client_admin, 'agency_user': agency_user, 'client_id': client_id}
    return jsonify(database.select_user_edit(auth_info=auth_info))

@api.route('/api/v1/google', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_google():
    GOOGLE_API_KEY = 'AIzaSyBc5gDqKJviHuqVJns1ZWctawtpro_zH1U'
    address = request.args.get('address')
    city = request.args.get('city').strip()
    state = request.args.get('state').strip()
    zipcode = request.args.get('zipcode').strip()
    keyword = request.args.get('name').strip()
    users_id = request.args.get('users_id').strip()

    if request.args.get('client_id'):
        if request.args.get('client_id') == 'null':
            client_id = str2bool(request.args.get('client_id'))
        else:
            client_id = request.args.get('client_id').strip()

    location = ', '.join([', '.join([address, zipcode.strip(), city]), state])
    query_result = None
    google_places = GooglePlaces(GOOGLE_API_KEY)
    if location and keyword:
        query_result = google_places.nearby_search(
            location=location, keyword=keyword)

    google_review_scans = []
    average_rating = None
    total_number = None
    city = None
    state = None
    lat = None
    lng = None

    if query_result:
        if query_result.has_attributions:
            print(query_result.html_attributions)
        if query_result.places:
            for place in query_result.places:
                place.get_details()
                if place.rating:
                    average_rating = place.rating
                if place.details:
                    if 'reviews' in place.details:
                        total_number = len(place.details['reviews'])
                    if 'geometry' in place.details:
                        lat = place.details['geometry']['location']['lat']
                        lng = place.details['geometry']['location']['lng']
                if place.vicinity:
                    city = place.vicinity
                if place.formatted_address:
                    state = place.formatted_address.split()[-1]
                google_review_info = {'average_rating': average_rating,
                                      'total_number': total_number,
                                      'city': city,
                                      'state': state,
                                      'name': keyword,
                                      'zipcode': zipcode,
                                      'lat': lat,
                                      'lng': lng,
                                      'users_id': users_id,
                                      'client_id': client_id
                                      }
                google_review_scans.append(google_review_info)

    return jsonify(database.select_scan_google(google_list=google_review_scans))

@api.route('/api/v1/csv_download', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_csv_download():
    request_url = request.url
    return jsonify(database.download_csv(request_url=request_url))

@api.route('/api/v1/google_list', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_google_list():
    data = database.select_google_list()
    return jsonify(data)

@api.route('/api/v1/google_analytics', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_google_analytics():
    analytics_id = request.args.get('analytics_id')
    data = database.select_google_analytics(analytics_id=analytics_id)
    return jsonify(data)

@api.route('/api/v1/google_edit', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_google_edit():
    GOOGLE_API_KEY = 'AIzaSyBc5gDqKJviHuqVJns1ZWctawtpro_zH1U'
    address = request.args.get('address')
    city = request.args.get('city').strip()
    state = request.args.get('state').strip()
    zipcode = request.args.get('zipcode').strip()
    keyword = request.args.get('name').strip()
    current_id = request.args.get('current_id')
    location = ', '.join([', '.join([address, zipcode.strip(), city]), state])
    query_result = None
    google_places = GooglePlaces(GOOGLE_API_KEY)
    if location and keyword:
        query_result = google_places.nearby_search(
            location=location, keyword=keyword)

    google_review_scans = []
    average_rating = None
    total_number = None
    city = None
    state = None
    if query_result:
        if query_result.has_attributions:
            print(query_result.html_attributions)
        if query_result.places:
            for place in query_result.places:
                place.get_details()

                if place.rating:
                    average_rating = place.rating
                if place.details:
                    if 'reviews' in place.details:
                        total_number = len(place.details['reviews'])
                if place.vicinity:
                    city = place.vicinity
                if place.formatted_address:
                    state = place.formatted_address.split()[-1]
                google_review_info = {'average_rating': average_rating,
                                      'total_number': total_number,
                                      'city': city,
                                      'state': state,
                                      'name': keyword,
                                      'zipcode': zipcode,
                                      'current_id': current_id
                                      }
                google_review_scans.append(google_review_info)

    return jsonify(database.select_google_reivew_edit(google_info=google_review_scans))

@api.route('/api/v1/google_stars', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_google_stars():
    GOOGLE_API_KEY = 'AIzaSyBc5gDqKJviHuqVJns1ZWctawtpro_zH1U'
    current_id = request.args.get('analytics_id')
    users_id = request.args.get('users_id')
    if request.args.get('client_id'):
        if request.args.get('client_id') == 'null':
            client_id = str2bool(request.args.get('client_id'))
        else:
            client_id = request.args.get('client_id').strip()

    data = database.select_google_analytics(analytics_id=current_id)
    address = data[0]['city']
    zipcode = data[0]['zipcode']
    state = data[0]['state']
    keyword = data[0]['name']
    location = ', '.join([', '.join([address, zipcode.strip()]), state])

    query_result = None
    google_places = GooglePlaces(GOOGLE_API_KEY)

    if location and keyword:
        query_result = google_places.nearby_search(
            location=location, keyword=keyword)
    google_review_scans = []
    reviews_info = []
    if query_result:
        if query_result.has_attributions:
            print(query_result.html_attributions)
        if query_result.places:
            for place in query_result.places:
                place.get_details()
                if place.details:
                    if 'reviews' in place.details:
                        reviews_info = place.details['reviews']

                if reviews_info:
                    for single_review in reviews_info:
                        star_1 = None
                        star_2 = None
                        star_3 = None
                        star_4 = None
                        star_5 = None
                        author_name = None
                        author_text = None
                        review_date = None

                        if single_review['rating'] == 1:
                            star_1 = single_review['rating']
                        if single_review['rating'] == 2:
                            star_2 = single_review['rating']
                        if single_review['rating'] == 3:
                            star_3 = single_review['rating']
                        if single_review['rating'] == 4:
                            star_4 = single_review['rating']
                        if single_review['rating'] == 5:
                            star_5 = single_review['rating']
                        if 'text' in single_review:
                            author_text = single_review['text']
                        if 'author_name' in single_review:
                            author_name = single_review['author_name']
                        if 'relative_time_description' in single_review:
                            review_date = single_review['relative_time_description']

                        google_review_info = {'star_1': star_1,
                                              'star_2': star_2,
                                              'star_3': star_3,
                                              'star_4': star_4,
                                              'star_5': star_5,
                                              'author_text': author_text,
                                              'author_name': author_name,
                                              'current_id': current_id,
                                              'listing_name': keyword,
                                              'review_date': review_date,
                                              'users_id': users_id,
                                              'client_id': client_id
                                              }
                        google_review_scans.append(google_review_info)

                else:
                    google_review_info = {'current_id': current_id, 'listing_name': keyword, 'users_id': users_id, 'client_id': client_id}
                    google_review_scans.append(google_review_info)

    data = jsonify(database.select_google_reivew_stars(google_info=google_review_scans))
    return data

@api.route('/api/v1/google_stars_list', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_google_stars_list():
    current_id = request.args.get('current_id')
    data = database.select_google_stars_list(current_id=current_id)
    return jsonify(data)

@api.route('/api/v1/google_stars_all_list', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_google_stars_all_list():
    data = database.select_google_stars_all_list()
    return jsonify(data)

@api.route('/api/v1/stars_remove', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_stars_remove():
    current_id = request.args.get('current_id')
    if current_id and current_id == 'null':
        current_id = str2bool(current_id)

    users_id = request.args.get('user_id')
    if users_id and users_id == 'null':
        users_id = str2bool(users_id)
    dict_data = {'users_id': users_id, 'current_id': current_id}
    data = database.select_stars_list_remove(dict_data)
    return jsonify(data)

@api.route('/api/v1/google_remove', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_google_remove():
    current_id = request.args.get('current_id')
    if current_id and current_id == 'null':
        current_id = str2bool(current_id)

    users_id = request.args.get('user_id')
    if users_id and users_id == 'null':
        users_id = str2bool(users_id)
    dict_data = {'users_id': users_id, 'current_id': current_id}
    data = database.select_google_list_remove(dict_data)
    return jsonify(data)

@api.route('/api/v1/google_stars_user', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_google_stars_user():
    data = database.select_google_stars_user()
    return jsonify(data)

@api.route('/api/v1/users_all', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_users_all():
    data = database.select_users_all()
    return jsonify(data)

@api.route('/api/v1/users_remove', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_users_remove():
    user_id = request.args.get('user_id')
    data = database.select_users_remove(user_id=user_id)
    return jsonify(data)

@api.route('/api/v1/stars_details', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_stars_details():
    stars_id = request.args.get('stars_id')
    data = database.select_stars_details(stars_id=stars_id)
    return jsonify(data)

@api.route('/api/v1/users_details', methods=['GET', 'POST', 'OPTIONS'])
@add_response_headers(cors=True)
def api_users_details():
    user_id = request.args.get('user_id')
    data = database.select_users_details(user_id=user_id)
    return jsonify(data)