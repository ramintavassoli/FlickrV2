drop database flickrV2;
create database flickrV2;
use FlickrV2;

CREATE TABLE users (
    uid INT AUTO_INCREMENT,
    first_name VARCHAR(20),
    last_name VARCHAR(20),
    email VARCHAR(100),
    dob DATE,
    hometown VARCHAR(20),
    gender CHAR(1),
    password VARCHAR(20),
    PRIMARY KEY (uid)
);

CREATE TABLE friendships (
    uid INTEGER,
    fid INTEGER,
    PRIMARY KEY (uid , fid)
);

CREATE TABLE albums (
    aid INT NOT NULL AUTO_INCREMENT,
    uid INTEGER,
    aname VARCHAR(20),
    doc DATE,
    PRIMARY KEY (aid)
);

CREATE TABLE photos (
    pid INT NOT NULL AUTO_INCREMENT,
    aid INTEGER,
    binary_data BLOB,
    caption VARCHAR(200),
    PRIMARY KEY (pid)
);

CREATE TABLE tags (
    tid INT NOT NULL AUTO_INCREMENT,
    pid INTEGER,
    uid INTEGER,
    tag VARCHAR(20),
    date_tagged DATE,
    PRIMARY KEY (tid , uid, pid)
);

CREATE TABLE comments (
    cid INT NOT NULL AUTO_INCREMENT,
    uid INTEGER,
    pid INTEGER,
    txt VARCHAR(200),
    date_commented DATE,
    PRIMARY KEY (cid , uid , pid)
);

CREATE TABLE likes (
    lid INT NOT NULL AUTO_INCREMENT,
    pid INTEGER,
    uid INTEGER,
    PRIMARY KEY (lid , pid , uid)
);

CREATE TABLE recommended_photos (
    binary_data BLOB,
    pid INT,
    caption VARCHAR(200)
);

ALTER TABLE friendships ADD FOREIGN KEY (uid) REFERENCES users(uid) on delete cascade;
ALTER TABLE friendships ADD FOREIGN KEY (fid) REFERENCES users(uid) on delete cascade;
ALTER TABLE albums ADD FOREIGN KEY (uid) REFERENCES users(uid) on delete cascade;
ALTER TABLE photos ADD FOREIGN KEY (aid) REFERENCES albums(aid) on delete  cascade;
ALTER TABLE comments ADD FOREIGN KEY (uid) REFERENCES users(uid) on delete cascade;
ALTER TABLE comments ADD FOREIGN KEY (pid) REFERENCES photos(pid) on delete cascade;
ALTER TABLE tags ADD FOREIGN KEY (pid) REFERENCES photos(pid) on delete cascade;
ALTER TABLE tags ADD FOREIGN KEY (uid) REFERENCES users(uid) on delete cascade;

Delimiter $$
CREATE TRIGGER tag_format BEFORE INSERT ON tags
FOR EACH ROW
BEGIN
IF (new.tag REGEXP BINARY '^[a-z][a-z]*[a-z]$') = 0 Then 
SIGNAL SQLSTATE '12345'
     SET MESSAGE_TEXT = 'Tag must be a single word all lowercased chars';
END IF;
END &&
Delimiter ;
