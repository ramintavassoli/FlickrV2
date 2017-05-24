######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
import time 

#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'pass'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '1234'
app.config['MYSQL_DATABASE_DB'] = 'flickrv2'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from users") 
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from users") 
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd 
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT uid FROM users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]
 
def add_friends(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT Concat(U.first_name, ' ',  U.last_name)\
                    From users U \
                    WHERE U.uid != '{0}' AND U.uid NOT IN \
                        (SELECT F.fid\
                          FROM friendships F, Users U \
                          WHERE F.uid = '{0}')\
                        ".format(uid))
    return cursor.fetchall()
                        
def get_friends(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT Concat(U.first_name, ' ',  U.last_name)\
                    From users U \
                    WHERE U.uid IN \
                        (SELECT F.fid \
                        FROM friendships F \
                        WHERE F.uid = '{0}')".format(uid))
    return cursor.fetchall()

@app.route("/view", methods=['GET'])
@flask_login.login_required
def view():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if len(get_friends(uid)) >0:
        return render_template('view.html', friends = get_friends(uid))
    else:
        return render_template('view.html', message = 'You have Zero friends')
        
@app.route("/add", methods=['GET', 'POST'])
@flask_login.login_required
def add():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == "GET":
        return render_template('add.html', potential = add_friends(uid))
    else:
        try:
            f_name=request.form.get('f_name')
            l_name=request.form.get('l_name')
            cursor = conn.cursor()
            cursor.execute("SELECT U.uid\
                            FROM users U\
                            WHERE U.first_name = '{0}' AND U.last_name = '{1}'".format(f_name,l_name))
            friend_fid= cursor.fetchone()[0]
            new_cursor = conn.cursor()
            new_cursor.execute("INSERT INTO friendships (uid, fid) VALUES ('{0}', '{1}')".format(uid,friend_fid))
            new_cursor.execute("INSERT INTO friendships (fid, uid) VALUES ('{0}', '{1}')".format(uid,friend_fid))
            conn.commit()
            return render_template('add.html', potential = add_friends(uid), message = "Add More!? If not go back to your profile for more options")
        except:
            return render_template('add.html', potential = add_friends(uid), message = 'Please enter legitimate names')
        
        
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
         email=request.form.get('email')
         password=request.form.get('password')
         dob=request.form.get('dob')
         first_name=request.form.get('first_name')
         last_name=request.form.get('last_name')
         hometown=request.form.get('hometown')
         gender=request.form.get('gender')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print cursor.execute("INSERT INTO users (email, password, dob, first_name, last_name, hometown, gender) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, dob, first_name, last_name, hometown, gender))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print "couldn't find all tokens"
		return flask.redirect(flask.url_for('register'))

#######################################Photos Functions##############################
def getUsersPhotosFromAlbum(uid,aid):
	cursor = conn.cursor()
	cursor.execute("SELECT binary_data, pid, caption FROM photos JOIN albums ON photos.aid = albums.aid WHERE albums.uid = '{0}' AND photos.aid = '{1}'".format(uid,aid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUsersPhotos(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT P.binary_data, P.pid, P.caption FROM photos P, albums A WHERE P.aid = A.aid AND A.uid IN (SELECT U.uid FROM users U WHERE U.uid = '{0}')".format(uid))
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getAllPhotos():
    cursor = conn.cursor()
    cursor.execute("SELECT binary_data, pid, caption FROM photos")
    return cursor.fetchall()

def getPhotosByTags(uid,tag):
    cursor = conn.cursor()
    cursor.execute("SELECT P.binary_data, P.pid, P.caption FROM photos P WHERE P.pid IN (SELECT T.pid FROM tags T WHERE T.uid = {0} AND T.tag = '{1}')".format(uid, tag))
    return cursor.fetchall()

def getPhotosByJustTags(tag):
    cursor = conn.cursor()
    cursor.execute("SELECT P.binary_data, P.pid, P.caption FROM photos P WHERE P.pid IN (SELECT T.pid FROM tags T WHERE T.tag = '{0}')".format(tag))
    return cursor.fetchall()
    

#####################################Photos Fucntions#################################
def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code
@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def get_albums(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT A.aname FROM albums A WHERE A.uid = '{0}'".format(uid))
    return cursor.fetchall()

def get_aid(aname):
    cursor = conn.cursor()
    cursor.execute("SELECT A.aid FROM albums A WHERE A.aname = '{0}'".format(aname))
    return cursor.fetchone()[0]

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        imgfile = request.files['photo']
        caption = request.form.get('caption')
        tag = request.form.get('tag_name')
        alb = request.form.get('album')
        print caption
        photo_data = base64.standard_b64encode(imgfile.read())
        cursor = conn.cursor()
        sys_time = time.strftime('%Y-%m-%d')
        if cursor.execute("SELECT A.aid FROM albums A WHERE A.aname = '{0}' AND A.uid = {1}".format(alb, uid)):
            aid = cursor.fetchone()[0]
            cursor.execute("INSERT INTO photos (binary_data, aid, caption) VALUES ('{0}', '{1}', '{2}')".format(photo_data, get_aid(alb), caption))
            conn.commit()      
            cursor.execute("SELECT P.pid FROM photos P WHERE P.binary_data = '{0}' AND aid = {1} AND caption = '{2}'".format(photo_data, get_aid(alb), caption))
            pid_this = cursor.fetchone()[0]            
            cursor.execute("INSERT INTO tags (pid, uid, tag, date_tagged) VALUES ({0}, {1}, '{2}', '{3}')".format(pid_this, uid, tag, sys_time))
            conn.commit()
            return render_template('upload.html', albums = get_albums(uid), message='Photo uploaded to existing album!')
        else:
            cursor.execute("INSERT INTO albums (uid, aname, doc) VALUES ('{0}','{1}','{2}')".format(uid, alb,sys_time))
            conn.commit()
            cursor.execute("INSERT INTO photos (binary_data, aid, caption) VALUES ('{0}', '{1}', '{2}')".format(photo_data, get_aid(alb), caption))
            conn.commit()
            cursor.execute("SELECT P.pid FROM photos P WHERE P.binary_data = '{0}' AND aid = {1} AND caption = '{2}'".format(photo_data, get_aid(alb), caption))
            pid_this = cursor.fetchone()[0]  
            cursor.execute("INSERT INTO tags (pid, uid, tag, date_tagged) VALUES ({0}, {1}, '{2}', '{3}')".format(pid_this, uid, tag, sys_time))
            conn.commit()
            return render_template('upload.html', albums = get_albums(uid), message='Photo uploaded to your new album!') 
	#The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('upload.html', albums = get_albums(uid))
#end photo uploading code 
def view_user_tags(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT T.tag FROM tags T WHERE T.uid = {0}".format(uid))
    return cursor.fetchall()

@app.route('/myphotos', methods=['GET', 'POST'])
@flask_login.login_required
def view_myphotos():
    uid_current = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        album_name=request.form.get('album')
        tag_return = request.form.get('tag_name')
        if album_name is not None:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT A.aid FROM albums A WHERE A.uid = {0} AND A.aname = '{1}'".format(uid_current,album_name))
                album_aid= cursor.fetchone()[0]
                return render_template('myphotos.html', albums = get_albums(uid_current), view_tags = view_user_tags(uid_current), photos = getUsersPhotosFromAlbum(uid_current, album_aid))
            except:
                return render_template('myphotos.html', albums = get_albums(uid_current), view_tags = view_user_tags(uid_current), message = 'Album name does not exist in the database!')
        elif tag_return is not None:
            try:
                return render_template('myphotos.html', albums = get_albums(uid_current), view_tags = view_user_tags(uid_current), photos = getPhotosByTags(uid_current, tag_return))
            except:
                return render_template('myphotos.html', albums = get_albums(uid_current), view_tags = view_user_tags(uid_current), message = 'Tag name does not exist in the database!')
    else:
        return render_template('myphotos.html', albums = get_albums(uid_current), view_tags = view_user_tags(uid_current))

def users_names():
    cursor = conn.cursor()
    cursor.execute("SELECT Concat(U.first_name, ' ',  U.last_name) From users U")
    return cursor.fetchall()
def tags_names():
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT T.tag from tags T")
    return cursor.fetchall()
def mostPoptags():
    cursor = conn.cursor()
    cursor.execute("SELECT T.tag from tags T GROUP BY T.tag ORDER BY COUNT(*) DESC LIMIT 5")
    return cursor.fetchall()

@app.route('/allphotos', methods=['POST','GET'])
def view_allphotos():
    if request.method == 'POST':
        ff_name=request.form.get('f_name')
        ll_name=request.form.get('l_name')
        tag_return=request.form.get('tag_name')
        cursor = conn.cursor()
        if ff_name is not None:
            try:
                cursor.execute("SELECT U.uid FROM users U WHERE U.first_name = '{0}' AND U.last_name = '{1}'".format(ff_name,ll_name))
                user_uid = cursor.fetchone()[0]
                return render_template('allphotos.html', photos = getUsersPhotos(user_uid), view_artists = users_names(), view_tags = tags_names(), view_most_pop_tags = mostPoptags(), message_two = "Follow the following set of directions to post comments")
            except:
                return render_template('allphotos.html', view_artists = users_names(), view_tags = tags_names(), view_most_pop_tags = mostPoptags(), message = 'Artist not found in the database!')
        elif tag_return is not None:
            try:
                tag_list = tag_return.split()
                photo_input = []
                for tag in tag_list:
                    photo_input.extend(getPhotosByJustTags(tag))
                return render_template('allphotos.html', photos = photo_input, view_artists = users_names(), view_tags = tags_names(), view_most_pop_tags = mostPoptags(),  message_two = "Follow the following set of directions to post comments")
            except:
                return render_template('allphotos.html', view_artists = users_names(), view_tags = tags_names(), view_most_pop_tags = mostPoptags(), message = 'Tag not found in the database!')
    else:
        return render_template('allphotos.html', view_artists = users_names(), view_tags = tags_names(), view_most_pop_tags = mostPoptags())

def read_all_photo_comments(pid):
    cursor = conn.cursor()
    cursor.execute("SELECT C.txt FROM comments C WHERE C.pid = '{0}'".format(pid))
    return cursor.fetchall()
    
def count_how_many_likes(pid):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM likes L WHERE L.pid = '{0}'".format(pid))
    return cursor.fetchone()[0]
    
def having_liked_test(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT L.uid FROM likes L WHERE L.uid = '{0}'".format(uid))
    return cursor.fetchone()[0]

@app.route('/comments', methods=['POST','GET'])
def view_add_comments():
    sys_time = time.strftime('%Y-%m-%d')
    uid_return = getUserIdFromEmail(flask_login.current_user.id)
    comment_return = request.form.get('comment')
    image_key = request.form.get('key')
    like_return = request.form.get('like')
    if request.method == "POST":
        cursor = conn.cursor()
        if comment_return is not None:
            cursor.execute("INSERT INTO comments (uid,pid,txt,date_commented) VALUES ({0}, {1}, '{2}', '{3}')".format(uid_return, int(image_key), comment_return, sys_time))
            conn.commit()
            return render_template('comments.html', comments = read_all_photo_comments(image_key))
        elif like_return is not None and uid_return is not None:
            if having_liked_test(uid_return) is None:
                cursor.execute("INSERT INTO likes (uid, pid) VALUES ('{0}', '{1}')".format(uid_return, like_return))
                conn.commit()                
                return render_template('comments.html', message = "Thank you for your input!!", comments = read_all_photo_comments(image_key), likes = count_how_many_likes(like_return))
            else:
                return render_template('comments.html', message = "You have liked this image before!!", comments = read_all_photo_comments(image_key), likes = count_how_many_likes(like_return))
        elif image_key is not None:
            return render_template('comments.html', comments = read_all_photo_comments(image_key), likes = count_how_many_likes(image_key))
    else:
        return render_template('comments.html')

def most_used_tag_user(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT T.tag from tags T WHERE T.uid = '{0}' GROUP BY T.tag ORDER BY COUNT(*) DESC LIMIT 5".format(uid))
    return cursor.fetchall()

def most_related_photos_by_tags():
    cursor = conn.cursor()
    cursor.execute("SELECT R.binary_data, R.pid, R.caption FROM recommended_photos R GROUP BY R.pid ORDER BY COUNT(*) DESC")
    return cursor.fetchall

@app.route('/recommendedPhotos', methods=['GET'])
@flask_login.login_required
def recommend_photos():
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS recommended_photos")
    cursor.execute("CREATE TABLE recommended_photos (binary_data BLOB, pid INT, caption VARCHAR(200));")
    uid = getUserIdFromEmail(flask_login.current_user.id)
    tag_tuple = most_used_tag_user(uid)
    tag_list = list(tag_tuple)
    for tag in tag_list:
        photo_tuple = getPhotosByJustTags(tag)
        photo_list = list(photo_tuple)
        cursor.execute("INSERT INTO recommended_photos (binary_data, pid, caption) VALUES ('{0}','{1}','{2}')".format(photo_list[0], photo_list[1], photo_list[2]))
        conn.commit()
    return render_template('recommendedPhotos.html', photos = most_related_photos_by_tags())

@app.route('/deletePhotos', methods=['POST','GET'])
@flask_login.login_required
def delete_photos():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        del_photo = request.form.get('pid')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM photos USING photos INNER JOIN albums INNER JOIN users WHERE photos.pid = {0} AND photos.aid = albums. aid AND albums.uid = {1}".format(int(del_photo), uid))
        conn.commit()        
        return render_template('deletePhotos.html', photos = getUsersPhotos(uid))
    else:
        return render_template('deletePhotos.html', photos = getUsersPhotos(uid))

@app.route('/deleteAlbums', methods=['POST','GET'])
@flask_login.login_required
def delete_albums():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        alb = request.form.get('album_name')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM albums WHERE albums.aname = '{0}' AND albums.uid = {1}".format(alb, uid))
        conn.commit()        
        return render_template('deleteAlbums.html',  albums = get_albums(uid))
    else:
        return render_template('deleteAlbums.html',  albums = get_albums(uid))
#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)