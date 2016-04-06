import sqlite3 , datetime, random
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, send_from_directory

from contextlib import closing
from werkzeug import secure_filename
import os
from PIL import Image

#config
DATABASE = 'entries.db'
UPLOAD_FOLDER = './img'
DEBUG = True
SECRET_KEY = 'dev key'
USERNAME = 'ryan'
PASSWORD = 'password'



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.from_object(__name__)
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

def init_db():
	with closing(connect_db()) as db:
		with app.open_resource('schema.db', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()
		
		
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif','PNG', 'JPG','JPEG','GIF'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	db = getattr(g, 'db', None)
	if db is not None:
		db.close()

@app.route('/entries')
def show_entries():
	if session.get('logged_in') and session['logged_in']==True:
		print 'Logged in :)', session['logged_in']
	else:
		return redirect(url_for('login'))
	cur = g.db.execute('select title,text,id from entries order by id desc')
	entries = [dict(title=row[0],text=row[1], id=row[2]) for row in cur.fetchall()]
	return render_template('entires.html', entries=entries)

@app.route('/')
def home():
	cur = g.db.execute('select title,text,id,creator from entries order by id desc')
	entries = [dict(title=row[0],text=row[1], id=row[2], creator=row[3]) for row in cur.fetchall()]
	return render_template('home.html', entries=entries)
	
@app.route('/create-account')
def account_new():
	return render_template('newaccount.html')	

@app.route('/create-account', methods=['POST'])
def create_account():
	print request
	file = request.files['file']
	if request.form['password'] != request.form['confirmpassword']:
		return render_template('newaccount.html', confirm = False)
	filename = ""
	if file and allowed_file(file.filename):
		filename = secure_filename(file.filename)
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	salt = str(random.randint(0,100000))
	password = hash(request.form['password']+salt)
	g.db.execute('insert into users (username,password, profilepic_name,date,salt) values (?,?,?,?,?)',
	[request.form['username'],password,filename, datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'), salt])
	
	g.db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))

@app.route('/add', methods=['POST'])
def add_entry():
	print request
	file = request.files['file']
	
	filename = ""
	if file and allowed_file(file.filename):
        	filename = secure_filename(file.filename)
        	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	g.db.execute('insert into entries (title,text,img_name,date, creator) values (?,?,?,?,?)',[request.form['title'],request.form['text'],filename, datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'), session['username']])

	g.db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))
	
@app.route('/edit', methods=['POST'])
def edit_entry():
	print 'edit', [request.form['title'],request.form['text'],request.form['id']]
	print request
	file = request.files['file']
	
	filename = ""
	if file and allowed_file(file.filename):
        	filename = secure_filename(file.filename)
        	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		g.db.execute('update entries set title=? ,text=? , date = ?, img_name=? where id=?',[request.form['title'],request.form['text'],datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'), filename,request.form['id']])
		g.db.commit()
	else:
		g.db.execute('update entries set title=? , text=?, date=?  where id=?',[request.form['title'],request.form['text'], datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'),request.form['id']])
		g.db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))
	
@app.route('/delete', methods=['POST'])
def del_entry():
	g.db.execute('delete from entries where id=(?)', (request.form['id'], ))
 	g.db.commit()
 	return redirect(url_for('show_entries'))

@app.route ('/login')
def login():
 	return render_template('login.html')
 	
@app.route('/login_info', methods=['POST'])
def login_info():
	user = g.db.execute('select username,password,salt from users where username == ?', [request.form['username']])
	user = [dict(username=row[0],password=row[1],salt=row[2]) for row in user.fetchall()]
	if user == []:
		return render_template('login.html', username=False)
	
	print user[0]['password'] 
	if user[0]['password'] == hash(request.form['password']+user[0]['salt']):
		session['logged_in'] = True
		session['username'] = user[0]['username']
	else:
		session['logged_in'] = False
	
	return redirect(url_for('show_entries'))	
	
	
@app.route('/entry/<id>')
def show_entry(id):
	cur = g.db.execute('select title,text,img_name, date, creator from entries where id == ?', [id])
	
	entries = [dict(title=row[0],text=row[1],img_name=row[2], date=row[3], creator=row[4]) for row in cur.fetchall()]
	if entries[0]['img_name'] != "":
		im = Image.open('img/'+entries[0]['img_name'])
		entries[0]['img_size'] = im.size
	print entries
	return render_template('entry.html', entry=entries[0])
	
	
@app.route('/edit/<id>')
def edit(id):
	if session['logged_in'] == False:
		return redirect(url_for('home'))		

	cur = g.db.execute('select title,text,id,date from entries where id == ?', [id])
	entries = [dict(title=row[0],text=row[1], id=row[2], date=row[3]) for row in cur.fetchall()]
# 	if entries[0]['img_name'] != "":
# 		im = Image.open('img/'+entries[0]['img_name'])
# 		entries[0]['img_size'] = im.size
	print entries
	return render_template('edit.html', entry=entries[0])
	
	
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)
		
@app.route('/log_out')
def log_out():
	session['logged_in'] = False
	return redirect(url_for("home"))	

if __name__ == '__main__':
	app.run()