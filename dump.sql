-- Users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL
);

-- Tor Data
CREATE TABLE tordata (
    date TIMESTAMP PRIMARY KEY,
    relays INT,
    bridges INT,
    torusers INT,
    onionlinks INT
);

DELETE FROM tordata;
INSERT INTO tordata (date, relays, bridges, torusers, onionlinks)
VALUES
  ('2023-01-08 00:00:00', 8751, 2487, 5050088, 798463),
  ('2023-01-09 00:00:00', 8742, 2479, 5050088, 798563),
  ('2023-01-10 00:00:00', 8745, 2481, 5050088, 798663),
  ('2023-01-11 00:00:00', 8750, 2484, 5050088, 798763),
  ('2023-01-12 00:00:00', 8741, 2482, 5050088, 798863),
  ('2023-01-13 00:00:00', 8744, 2483, 5050088, 798963),
  ('2023-01-14 00:00:00', 8747, 2484, 5050088, 799063),
  ('2023-01-15 00:00:00', 8742, 2481, 5050088, 799163),
  ('2023-01-16 00:00:00', 8745, 2482, 5050088, 799263),
  ('2023-01-17 00:00:00', 8748, 2484, 5050088, 799363);
  
-- Keywords
CREATE TABLE keywords (
    id SERIAL PRIMARY KEY,
    keywords VARCHAR(255) NOT NULL
);

-- DorkedLinks
CREATE TABLE dorkedlinks (
    id SERIAL PRIMARY KEY,
    link VARCHAR(255) NOT NULL
);

-- Onion Links
CREATE TABLE onionlinks (
    id SERIAL PRIMARY KEY,
    link VARCHAR(255) NOT NULL
);


-- Tor Relay IP Data
CREATE TABLE torrelayipdata (
    id serial PRIMARY KEY,
    name VARCHAR(255),
    ip_address VARCHAR(15),
    city VARCHAR(255),
    country VARCHAR(255),
    continent VARCHAR(255),
    latitude NUMERIC,
    longitude NUMERIC,
    isp VARCHAR(255),
    fingerprint VARCHAR(255),
    last_seen TIMESTAMP,
    last_changed_address_or_port TIMESTAMP,
    first_seen TIMESTAMP,
    running BOOLEAN,
    flags VARCHAR(255),
    consensus_weight INTEGER,
    contact VARCHAR,
    platform VARCHAR(255),
    guard_probability NUMERIC(28, 18),
    middle_probability NUMERIC(28, 18),
    exit_probability NUMERIC(28, 18)
);
