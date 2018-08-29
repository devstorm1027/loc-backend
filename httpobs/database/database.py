from contextlib import contextmanager
from types import SimpleNamespace
from os import getpid
from flask import session
from hashlib import md5

from httpobs.conf import (DATABASE_CA_CERT,
                          DATABASE_DB,
                          DATABASE_HOST,
                          DATABASE_PASSWORD,
                          DATABASE_PORT,
                          DATABASE_SSL_MODE,
                          DATABASE_USER)

import psycopg2
import psycopg2.extras
import psycopg2.pool
import sys
import csv
import urllib.request
from gi.repository import GLib

class SimpleDatabaseConnection:
    def __init__(self):
        self._initialized_pid = getpid()
        self._connected = True
        self._connect()

    def _connect(self):
        try:
            self._conn = psycopg2.connect(database=DATABASE_DB,
                                          host=DATABASE_HOST,
                                          password=DATABASE_PASSWORD,
                                          port=DATABASE_PORT,
                                          sslmode=DATABASE_SSL_MODE,
                                          sslrootcert=DATABASE_CA_CERT,
                                          user=DATABASE_USER)

            if not self._connected:
                print('INFO: Connected to PostgreSQL', file=sys.stderr)
            self._connected = True

        except:
            self._conn = SimpleNamespace(closed=1)

            if self._connected:
                print('WARNING: Disconnected from PostgreSQL', file=sys.stderr)
            self._connected = False

    @property
    def conn(self):
        # TLS connections cannot be shared across workers; you'll get a decryption failed or bad mac error
        # What we will do is detect if we're running in a different PID and reconnect if so
        # TODO: use celery's worker init stuff instead?
        if self._initialized_pid != getpid():
            self.__init__()

        # If the connection is closed, try to reconnect and raise an IOError if it's unsuccessful
        if self._conn.closed:
            self._connect()

            if self._conn.closed:
                raise IOError

        return self._conn

# Create an initial database connection on startup
db = SimpleDatabaseConnection()

@contextmanager
def get_cursor():
    try:
        yield db.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            db.conn.commit()
        except:
            db.conn.rollback()
    except:
        raise IOError


# Print out a warning on startup if we can't connect to PostgreSQL
try:
    with get_cursor() as _:  # noqa
        pass
except IOError:
    print('WARNING: Unable to connect to PostgreSQL.', file=sys.stderr)

def select_register(auth_info: {}) -> dict:
    with get_cursor() as cur:
        email = auth_info['email']
        session['email'] = email
        password = md5(auth_info['password'].encode('utf-8')).hexdigest()
        session['password'] = password
        super_admin = auth_info['super_admin']
        client_admin = auth_info['client_admin']
        agency_user = auth_info['agency_user']
        client_id = auth_info['client_id']
        cur.execute("""SELECT * FROM users
                                         WHERE email = (%s)
                                         ORDER BY creation_time DESC
                                         LIMIT 1""",
                    (session['email'],))
        if cur.rowcount > 0:
            message = session['email'] + " " + "is already a user in this account."
            status = False
            rows = dict(cur.fetchone(), message=message, status=status)
        else:
            cur.execute("""INSERT INTO users (email, password, super_adm, client_adm, agency_user, client_id, creation_time)
                                                 VALUES (%s, %s, %s, %s, %s, %s, NOW())
                                                 RETURNING *""", (session['email'], session['password'],
                                                                  super_admin, client_admin, agency_user, client_id))

            if cur.rowcount > 0:
                message = 'Created the New Account Successfully'
                status = True
                rows = dict(cur.fetchone(), message=message, status=status)
        return rows
    return {}

def select_login(login_info: {}) -> dict:
    with get_cursor() as cur:
        email = login_info['email']
        password = login_info['password']
        user_id = None
        agency_user = None
        super_admin = None
        client_id = None
        client_admin = None
        cur.execute("""SELECT * FROM users
                                         WHERE email = (%s)
                                         ORDER BY creation_time DESC
                                         LIMIT 1""",
                    (email,))

        if cur.rowcount > 0:
            rows = cur.fetchall()
            for row in rows:
                if md5(password.encode('utf-8')).hexdigest() == row[2]:
                    session['email'] = email
                    session['logged_in'] = True
                    message = 'Signed In Successfully'
                    user_id = row[0]
                    super_admin = row[3]
                    client_admin = row[4]
                    agency_user = row[5]
                    client_id = row[6]
                else:
                    session['logged_in'] = False
                    message = 'Invalid Email and Password'
        else:
            session['logged_in'] = False
            message = 'Invalid Email and Password'
        return dict(session, message=message, user_id=user_id, super_admin=super_admin,
                    client_admin=client_admin, agency_user=agency_user, client_id=client_id)
    return {}

def select_logout() -> dict:
    session.pop()
    message = 'Logged out Successfully'
    return {'message': message}

def select_users_all() -> dict:
    row_list = []
    with get_cursor() as cur:
        cur.execute("""SELECT * FROM users""")
        if cur.rowcount > 0:
            rows = cur.fetchall()
            for row in rows:
                row_info = {'user_id': row[0],
                            'email': row[1],
                            'super_admin': row[3],
                            'client_admin': row[4],
                            'agency_user': row[5],
                            'client_id': row[6]
                            }
                row_list.append(row_info)
    return row_list

def select_users_remove(user_id: str) -> dict:
    with get_cursor() as cur:
        cur.execute("""DELETE FROM users
                                     WHERE id = (%s)""",
                    (user_id,))
    return

def select_user_edit(auth_info: {}) -> dict:
    with get_cursor() as cur:
        if auth_info:
            session['email'] = auth_info['email']
            password = md5(auth_info['password'].encode('utf-8')).hexdigest()
            session['password'] = password
            client_admin = auth_info['client_admin']
            agency_user = auth_info['agency_user']
            client_id = auth_info['client_id']
            cur.execute("""UPDATE users SET (email, password, client_adm, agency_user, client_id, creation_time) =
                                             (%s, %s, %s, %s, %s, NOW())
                                             WHERE id = %s
                                             RETURNING *""",
                        (session['email'],
                         session['password'],
                         client_admin, agency_user, client_id,
                         auth_info['user_id']))

            if cur.rowcount > 0:
                rows = dict(cur.fetchone())
            return rows
    return {}

def select_scan_google(google_list: {}) -> dict:
    # Insert test result to the database
    # output_dir_path = "/home/ubuntu/products.csv"
    output_dir_path = "/home/golden/products.csv"
    fieldnames = ['Identifier', 'Total Number', 'Star Number',
                  'Average Rating', 'City']

    csv_file = open(output_dir_path, 'w')
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()

    with get_cursor() as cur:
        if google_list:
            if not google_list[0]['average_rating']:
                google_list[0]['average_rating'] = None
            cur.execute("""INSERT INTO google (total_number, star_number, average_rating, state, city, review_name, zipcode, lat, lng, client_id, users_id, creation_time)
                                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                                     RETURNING *""", (google_list[0]['total_number'],
                                                      '1',
                                                      google_list[0]['average_rating'],
                                                      google_list[0]['state'],
                                                      google_list[0]['city'],
                                                      google_list[0]['name'],
                                                      google_list[0]['zipcode'],
                                                      google_list[0]['lat'],
                                                      google_list[0]['lng'],
                                                      google_list[0]['client_id'],
                                                      google_list[0]['users_id']))

        # try:
        #     write_row = {'Identifier': google_list[0]['state'],
        #                  'Total Number': google_list[0]['total_number'],
        #                  'Star Number': google_list[0]['star_number'],
        #                  'Average Rating': google_list[0]['average_rating'],
        #                  'City': google_list[0]['city']}
        #     csv_writer.writerow(write_row)
        #
        # except:
        #     continue
        # pdb.set_trace()
            if cur.rowcount > 0:
                rows = dict(cur.fetchone())
            return rows
    return {}

def download_csv(request_url: str):
    downloads_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
    try:
        response = urllib.request.urlopen("file:///home/mufasa/Workspace/CSV/products.csv")
        if response:
            csv = response.read()
            with open(downloads_dir + '/google.csv', "wb") as code:
                code.write(csv)
        else:
            print("Don't exist CSV file")
    except:
        print("Unexpected error:", sys.exc_info()[0])

def select_google_list() -> dict:
    row_list = []
    with get_cursor() as cur:
        cur.execute("""SELECT * FROM google""")
        if cur.rowcount > 0:
            rows = cur.fetchall()
            for row in rows:
                row_info = {'total_number': row['total_number'],
                            'star_number': row['star_number'],
                            'average_rating': row['average_rating'],
                            'state': row['state'],
                            'city': row['city'],
                            'name': row['review_name'],
                            'id': row['id'],
                            'users_id': row['users_id'],
                            'client_id': row['client_id']
                            }
                row_list.append(row_info)
    return row_list

def select_google_analytics(analytics_id: str) -> dict:
    # pdb.set_trace()
    row_list = []
    with get_cursor() as cur:
        cur.execute("""SELECT * FROM google
                                 WHERE id = (%s)
                                 ORDER BY creation_time DESC
                                 LIMIT 1""",
                    (analytics_id,))
        if cur.rowcount > 0:
            rows = cur.fetchall()
            for row in rows:
                row_info = {'total_number': row['total_number'],
                            'star_number': row['star_number'],
                            'average_rating': row['average_rating'],
                            'state': row['state'],
                            'city': row['city'],
                            'name': row['review_name'],
                            'zipcode': row['zipcode'],
                            'id': row['id'],
                            'lat': row['lat'],
                            'lng': row['lng']
                            }
                row_list.append(row_info)
    return row_list

def select_google_reivew_edit(google_info: {}) -> dict:
    with get_cursor() as cur:
        if google_info:
            cur.execute("""UPDATE google SET (total_number, star_number, average_rating, state, city, review_name, zipcode, creation_time) =
                                             (%s, %s, %s, %s, %s, %s, %s, NOW())
                                             WHERE id = %s
                                             RETURNING *""",
                        (google_info[0]['total_number'],
                         1,
                         google_info[0]['average_rating'],
                         google_info[0]['state'],
                         google_info[0]['city'],
                         google_info[0]['name'],
                         google_info[0]['zipcode'],
                         google_info[0]['current_id']))
            if cur.rowcount > 0:
                rows = dict(cur.fetchone())
            return rows
    return {}

def select_google_reivew_stars(google_info: {}) -> dict:
    with get_cursor() as cur:
        star_1 = None
        star_2 = None
        star_3 = None
        star_4 = None
        star_5 = None
        author_name = None
        author_text = None
        review_date = None

        if google_info:
            for single_google_info in google_info:
                if 'current_id' in single_google_info:
                    current_id = single_google_info['current_id']
                if 'star_1' in single_google_info:
                    star_1 = single_google_info['star_1']
                if 'star_2' in single_google_info:
                    star_2 = single_google_info['star_2']
                if 'star_3' in single_google_info:
                    star_3 = single_google_info['star_3']
                if 'star_4' in single_google_info:
                    star_4 = single_google_info['star_4']
                if 'star_5' in single_google_info:
                    star_5 = single_google_info['star_5']
                if 'author_name' in single_google_info:
                    author_name = single_google_info['author_name']
                if 'author_text' in single_google_info:
                    author_text = single_google_info['author_text']
                if 'review_date' in single_google_info:
                    review_date = single_google_info['review_date']
                if 'listing_name' in single_google_info:
                    listing_name = single_google_info['listing_name']
                users_id = single_google_info['users_id']
                client_id = single_google_info['client_id']

                cur.execute("""INSERT INTO stars (google_id, star_1, star_2, star_3, star_4, star_5, reviewer, review_description, listing_name, review_date, client_id, users_id, creation_time)
                                                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                                                     RETURNING *""", (current_id, star_1, star_2, star_3, star_4, star_5,
                                                                      author_name, author_text, listing_name, review_date, client_id, users_id),)
            if cur.rowcount > 0:
                rows = dict(cur.fetchone())
            return rows
    return {}

def select_google_stars_list(current_id: str) -> dict:
    row_list = []
    with get_cursor() as cur:
        cur.execute("""SELECT * FROM stars
                                 WHERE google_id = (%s)""",
                    (current_id,))

        if cur.rowcount > 0:
            rows = cur.fetchall()
            for row in rows:
                row_info = {'star_1': row['star_1'],
                            'star_2': row['star_2'],
                            'star_3': row['star_3'],
                            'star_4': row['star_4'],
                            'star_5': row['star_5'],
                            'reviewer': row['reviewer'],
                            'review_description': row['review_description'],
                            'google_id': row['google_id'],
                            'listing_name': row['listing_name'],
                            'review_date': row['review_date']
                            }
                row_list.append(row_info)
    return row_list

def select_google_stars_all_list() -> dict:
    row_list = []
    with get_cursor() as cur:
        cur.execute("""SELECT * FROM stars""")
        if cur.rowcount > 0:
            rows = cur.fetchall()
            for row in rows:
                row_info = {'star_1': row['star_1'],
                            'star_2': row['star_2'],
                            'star_3': row['star_3'],
                            'star_4': row['star_4'],
                            'star_5': row['star_5'],
                            'reviewer': row['reviewer'],
                            'review_description': row['review_description'],
                            'google_id': row['google_id'],
                            'listing_name': row['listing_name'],
                            'review_date': row['review_date']
                            }
                row_list.append(row_info)
    return row_list

def select_stars_list_remove(data: {}) -> dict:
    with get_cursor() as cur:
        current_id = data['current_id']
        users_id = data['users_id']
        if current_id:
            cur.execute("""DELETE FROM stars
                                         WHERE google_id = (%s)""",
                        (current_id,))
        elif users_id:
            cur.execute("""DELETE FROM stars
                                         WHERE users_id = (%s)""",
                        (users_id,))
    return

def select_google_list_remove(data: {}) -> dict:
    with get_cursor() as cur:
        current_id = data['current_id']
        users_id = data['users_id']
        if current_id:
            cur.execute("""DELETE FROM google
                                         WHERE id = (%s)""",
                        (current_id,))
        elif users_id:
            cur.execute("""DELETE FROM google
                                         WHERE users_id = (%s)""",
                        (users_id,))
    return

def select_google_stars_user() -> dict:
    row_list = []
    with get_cursor() as cur:
        cur.execute("""SELECT * FROM stars""")

        if cur.rowcount > 0:
            rows = cur.fetchall()
            for row in rows:
                row_info = {'star_1': row['star_1'],
                            'star_2': row['star_2'],
                            'star_3': row['star_3'],
                            'star_4': row['star_4'],
                            'star_5': row['star_5'],
                            'reviewer': row['reviewer'],
                            'review_description': row['review_description'],
                            'google_id': row['google_id'],
                            'listing_name': row['listing_name'],
                            'review_date': row['review_date'],
                            'users_id': row['users_id'],
                            'client_id': row['client_id']
                            }
                row_list.append(row_info)
    return row_list

def select_stars_details(stars_id: str) -> dict:
    row_list = []
    with get_cursor() as cur:
        cur.execute("""SELECT * FROM stars
                                     WHERE id = (%s)""",
                    (stars_id,))

        if cur.rowcount > 0:
            rows = cur.fetchall()
            for row in rows:
                row_info = {'star_1': row['star_1'],
                            'star_2': row['star_2'],
                            'star_3': row['star_3'],
                            'star_4': row['star_4'],
                            'star_5': row['star_5'],
                            'reviewer': row['reviewer'],
                            'review_description': row['review_description'],
                            'google_id': row['google_id'],
                            'listing_name': row['listing_name'],
                            'review_date': row['review_date']
                            }
                row_list.append(row_info)
    return row_list

def select_users_details(user_id: str) -> dict:
    row_list = []
    with get_cursor() as cur:
        cur.execute("""SELECT * FROM users
                                     WHERE id = (%s)""",
                    (user_id,))
        if cur.rowcount > 0:
            rows = cur.fetchall()
            for row in rows:
                row_info = {'user_id': row[0],
                            'email': row[1],
                            'super_admin': row[3],
                            'client_admin': row[4],
                            'agency_user': row[5],
                            'client_id': row[6]
                            }
                row_list.append(row_info)
    return row_list