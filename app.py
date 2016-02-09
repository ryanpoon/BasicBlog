import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from contextlib import closing

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
		
		
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
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
	cur = g.db.execute('select title,text,id from entries order by id desc')
	entries = [dict(title=row[0],text=row[1], id=row[2]) for row in cur.fetchall()]
	return render_template('home.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
	print request
	file = request.files['file']
	
	filename = ""
	if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
	g.db.execute('insert into entries (title,text,img_name) values (?,?,?)',[request.form['title'],request.form['text'],filename])
	g.db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))

@app.route ('/login')
def login():
 	return render_template('login.html')
 	
@app.route('/login_info', methods=['POST'])
def login_info():
	if USERNAME == request.form['username'] and	PASSWORD == request.form['password']:
		session['logged_in'] = True
	else:
		session['logged_in'] = False
	return redirect(url_for('show_entries'))	
	
	
@app.route('/entry/<id>')
def show_entry(id):
	cur = g.db.execute('select title,text from entries where id == ?', [id])
	entries = [dict(title=row[0],text=row[1]) for row in cur.fetchall()]
	print entries
	return render_template('entry.html', entry=entries[0])
	
		
@app.route('/log_out')
def log_out():
	session['logged_in'] = False
	return redirect(url_for("home"))	

if __name__ == '__main__':
	app.run()