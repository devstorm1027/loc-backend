CREATE TABLE IF NOT EXISTS users(
  id                                  SERIAL PRIMARY KEY,
  email                               VARCHAR NULL,
  password                            VARCHAR NULL,
  super_adm                           BOOLEAN NULL,
  client_adm                          BOOLEAN NULL,
  agency_user                         BOOLEAN NULL,
  client_id                           INTEGER NULL,
  creation_time                       TIMESTAMP NULL
);
CREATE TABLE IF NOT EXISTS google (
  id                                  SERIAL PRIMARY KEY,
  users_id                           INTEGER REFERENCES users (id) NOT NULL,
  total_number                        INTEGER NULL,
  star_number                         INTEGER NULL,
  average_rating                      FLOAT NULL,
  state                               VARCHAR NULL,
  city                                VARCHAR NULL,
  review_name                         VARCHAR NULL,
  zipcode                             VARCHAR NULL,
  lat                                 FLOAT NULL,
  lng                                 FLOAT NULL,
  client_id                           INTEGER NULL,
  creation_time                       TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS stars (
  id                                  SERIAL PRIMARY KEY,
  google_id                           INTEGER REFERENCES google (id) NOT NULL,
  users_id                           INTEGER REFERENCES users (id) NOT NULL,
  star_1                              INTEGER NULL,
  star_2                              INTEGER NULL,
  star_3                              INTEGER NULL,
  star_4                              INTEGER NULL,
  star_5                              INTEGER NULL,
  reviewer                            VARCHAR NULL,
  review_description                  VARCHAR NULL,
  listing_name                        VARCHAR NULL,
  review_date                         VARCHAR NULL,
  client_id                           INTEGER NULL,
  creation_time                       TIMESTAMP NULL
);

CREATE INDEX users_email_idx       ON users (email);
CREATE INDEX users_password_idx    ON users (password);
CREATE INDEX users_super_adm_idx    ON users (super_adm);
CREATE INDEX users_client_adm_idx    ON users (client_adm);
CREATE INDEX users_agency_user_idx    ON users (agency_user);
CREATE INDEX users_client_id_idx    ON users (client_id);

CREATE INDEX google_users_id_idx       ON google (users_id);
CREATE INDEX google_total_number_idx   ON google (total_number);
CREATE INDEX google_star_number_idx    ON google (star_number);
CREATE INDEX google_average_rating_idx ON google (average_rating);
CREATE INDEX google_state_idx          ON google (state);
CREATE INDEX google_city_idx           ON google (city);
CREATE INDEX google_review_name_idx    ON google (review_name);
CREATE INDEX google_zipcode_idx        ON google (zipcode);
CREATE INDEX google_lat_idx            ON google (lat);
CREATE INDEX google_lng_idx            ON google (lng);
CREATE INDEX google_client_id          ON google (client_id);

CREATE INDEX stars_users_id_idx                  ON stars (users_id);
CREATE INDEX stars_google_id_idx                 ON stars (google_id);
CREATE INDEX stars_star_1_idx                    ON stars (star_1);
CREATE INDEX stars_star_2_idx                    ON stars (star_2);
CREATE INDEX stars_star_3_idx                    ON stars (star_3);
CREATE INDEX stars_star_4_idx                    ON stars (star_4);
CREATE INDEX stars_star_5_idx                    ON stars (star_5);
CREATE INDEX stars_reviewer_idx                  ON stars (reviewer);
CREATE INDEX stars_review_description_idx        ON stars (review_description);
CREATE INDEX stars_listing_name_idx              ON stars (listing_name);
CREATE INDEX stars_review_date_idx               ON stars (review_date);
CREATE INDEX stars_client_id                     ON stars (client_id);

CREATE USER httpobsscanner;
GRANT SELECT on users, google, stars TO httpobsscanner;
GRANT UPDATE on users, google, stars TO httpobsscanner;
GRANT INSERT on users, google, stars TO httpobsscanner;
GRANT USAGE ON SEQUENCE users_id_seq TO httpobsscanner;
GRANT USAGE ON SEQUENCE google_id_seq TO httpobsscanner;
GRANT USAGE ON SEQUENCE stars_id_seq TO httpobsscanner;

CREATE USER httpobsapi;
GRANT SELECT ON users, google, stars to httpobsapi;
GRANT INSERT ON users, google, stars TO httpobsapi;
GRANT UPDATE ON users, google, stars TO httpobsapi;
GRANT USAGE ON SEQUENCE users_id_seq TO httpobsapi;
GRANT USAGE ON SEQUENCE google_id_seq TO httpobsapi;
GRANT USAGE ON SEQUENCE stars_id_seq TO httpobsapi;
