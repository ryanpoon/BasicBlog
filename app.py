import sqlite3 , datetime, random, smtplib, string
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, send_from_directory
from validate_email import validate_email
from contextlib import closing
from werkzeug import secure_filename
import os
from PIL import Image

#config
DATABASE = 'entries.db'
UPLOAD_FOLDER = './img'
DEBUG = True
SECRET_KEY = 'dev key'


with open('supersecretemail.txt', 'rb') as f:
	USERNAME = f.readline().strip()
	PASSWORD = f.readline().strip()

print USERNAME
print PASSWORD

#setup
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



#entries
@app.route('/entries')
def show_entries():
	if session.get('logged_in') and session['logged_in']==True:
		print 'Logged in :)', session['logged_in']
	else:
		return redirect(url_for('login'))
	cur = g.db.execute('select title,text,id from entries where creator == ? order by id desc', [session['username']])
	entries = [dict(title=row[0],text=row[1], id=row[2]) for row in cur.fetchall()]
	return render_template('entires.html', entries=entries)
#home
@app.route('/')
def home():
	cur = g.db.execute('select title,text,id,creator from entries order by id desc')
	entries = [dict(title=row[0],text=row[1], id=row[2], creator=row[3]) for row in cur.fetchall()]
	return render_template('home.html', entries=entries)
#createaccount
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
	g.db.execute('insert into users (username,password, profilepic_name,date,salt, last_active) values (?,?,?,?,?,?)',
	[request.form['username'],password,filename, datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'), salt, datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p')])
	
	g.db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))
	
#change password
@app.route('/changepswd')
def changepswd():
	return render_template('changepassword.html')
	
	
@app.route('/changepassword', methods=['POST'])
def changepassword():	
	user = g.db.execute('select username,password,salt from users where username == ?', [session['username']])
	user = [dict(username=row[0],password=row[1],salt=row[2]) for row in user.fetchall()]

	if hash(request.form['oldpassword']+user[0]['salt']) != user[0]['password']:
		return render_template('changepassword.html', wrong = True)
	if request.form['newpassword'] != request.form['confirmpassword']:
		return render_template('changepassword.html', confirm = False)
	password = request.form['newpassword']
	g.db.execute('update users set password=? where username==?',
	[hash(password+user[0]['salt']), session['username']])
	
	g.db.commit()
	return redirect(url_for('myprofile'))
	
#add email
@app.route('/email')
def addemail():
	return render_template('email.html')
@app.route('/addemail', methods=['POST'])
def addeml():
	user = g.db.execute('select username,password,salt from users where username == ?', [session['username']])
	user = [dict(username=row[0],password=row[1],salt=row[2]) for row in user.fetchall()]
	if hash(request.form['password']+user[0]['salt']) != user[0]['password']:
		return render_template('email.html', wrong = True)
	email = request.form['email']
	
	user = g.db.execute('select email from users where email == ?', [email])
	user = [1 for row in user.fetchall()]
	if user != []:
		return render_template('email.html', unique = False)
	if validate_email(email, verify=True) == True:
		
		g.db.execute('update users set email=? where username==?',[email, session['username']])
		g.db.commit()
		return redirect(url_for('myprofile'))
	else:
		return render_template('email.html', invalid = True)

	
	

#profile
@app.route('/myprofile')
def myprofile():
	user = g.db.execute('select username,profilepic_name,date,last_active,id,description from users where username == ?', [session['username']])
	user = [dict(username=row[0],profilepic_name=row[1],date=row[2],last_active=row[3],id=row[4],description=row[5]) for row in user.fetchall()]
	if session['logged_in'] == False:
		return redirect(url_for('home'))	
	if user[0]['description'] == None:
		user[0]['description'] = 'You haven\'t written a description yet! Go ahead and click here to start writing!'
	return render_template('profilepage.html', user=user[0])


#new entry
@app.route('/add', methods=['POST'])
def add_entry():
	print request
	file = request.files['file']
	
	filename = ""
	if file and allowed_file(file.filename):
        	filename = secure_filename(file.filename)
        	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	g.db.execute('insert into entries (title,text,img_name,date, creator) values (?,?,?,?,?)',[request.form['title'],request.form['text'],filename, datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'), session['username']])
	g.db.execute('update users set last_active = ? where username=?', [datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'), session['username']])
	g.db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))
#edit
@app.route('/edit', methods=['POST'])
def edit_entry():
	print 'edit', [request.form['title'],request.form['text'],request.form['id']]
	print request
	file = request.files['file']
	
	filename = ""
	if file and allowed_file(file.filename):
        	filename = secure_filename(file.filename)
        	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		g.db.execute('update users set last_active = ? where username=?', [datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'), session['username']])
		g.db.execute('update entries set title=? ,text=? , date = ?, img_name=? where id=?',[request.form['title'],request.form['text'],datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'), filename,request.form['id']])
		g.db.commit()
	else:
		g.db.execute('update entries set title=? , text=?, date=?  where id=?',[request.form['title'],request.form['text'], datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'),request.form['id']])
		g.db.execute('update users set last_active = ? where username=?', [datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'), session['username']])
		g.db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('show_entries'))
#delete
@app.route('/delete', methods=['POST'])
def del_entry():
	g.db.execute('delete from entries where id=(?)', (request.form['id'], ))
	g.db.execute('update users set last_active = ? where username=?', [datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'), session['username']])
 	g.db.commit()
 	return redirect(url_for('show_entries'))
#login
@app.route('/login')
def login():
 	return render_template('login.html')
 	
#change profile pic
@app.route('/profpic', methods=['POST'])
def change_profpic():
	file = request.files['file']
	
	filename = ""
	if file and allowed_file(file.filename):
        	filename = secure_filename(file.filename)
        	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		g.db.execute('update users set profilepic_name=? where id=?',[filename, request.form['id']])
		g.db.execute('update users set last_active = ? where username=?', [datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'), session['username']])
		g.db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('myprofile'))
#change profile description
@app.route('/profdesc', methods=['POST'])
def changeprofdesc():

	
	g.db.execute('update users set description=? where id=?',[request.form['text'], request.form['id']])
	g.db.execute('update users set last_active = ? where username=?', [datetime.datetime.today().strftime('%m/%d/%Y at %I:%M %p'), session['username']])
	g.db.commit()
	flash('New entry was successfully posted')
	return redirect(url_for('myprofile'))
#logging in
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
		return render_template('login.html', password=False)
	
	return redirect(url_for('show_entries'))	

#forgot my password!
@app.route('/forgotpassword')
def forgotpassword():
	return render_template('forgotpassword.html')
	
@app.route('/sendeml', methods=['POST'])
def sendeml():
	user = g.db.execute('select email, username from users where email == ?', [request.form['email']])
	user = [dict(email=row[0], username=row[1]) for row in user.fetchall()]
	if user==[]:
		return render_template('forgotpassword.html', noemail = True)
	else:
		randomcode = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
		g.db.execute('update users set randomcode=? where username=?', [randomcode, user[0]['username']])
		g.db.commit()
		print randomcode	
		smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
		smtpObj.ehlo()
		print 'echo'
		smtpObj.starttls()
		smtpObj.login(USERNAME, PASSWORD)
		print 'login'
		smtpObj.sendmail(USERNAME, user[0]['email'],
        'Subject: Please Verify Your Password Change\nDear '+user[0]['username']+',\nYour code to change your password is '+ randomcode)
		print 'sent'
		smtpObj.quit()
		return render_template('forgotpassword2.html', email=user[0]['email'])
		
		
@app.route('/submitcode', methods=['POST'])
def submitcode():
	user = g.db.execute('select email, username, randomcode from users where email == ?', [request.form['email']])
	user = [dict(email=row[0], username=row[1], randomcode=row[2]) for row in user.fetchall()]
	if request.form['code'] != user[0]['randomcode']:
		return render_template('forgotpassword2.html', wrong = True,  email=user[0]['email'])
	else:
		return render_template('forgotpassword3.html', email=user[0]['email'])
	return 
@app.route('/changepasswordforgot', methods=['POST'])	
def changepasswordforgot():
	user = g.db.execute('select username,password,salt from users where email == ?', [request.form['email']])
	user = [dict(username=row[0],password=row[1],salt=row[2]) for row in user.fetchall()]

	if request.form['newpassword'] != request.form['confirmpassword']:
		return render_template('forgotpassword3.html', confirm = False, email=request.form['email'])
	password = request.form['newpassword']
	g.db.execute('update users set password=? where email==?',
	[hash(password+user[0]['salt']), request.form['email']])
	
	g.db.commit()
	return redirect(url_for('myprofile'))
		
#going to specific entry	
@app.route('/entry/<id>')
def show_entry(id):
	cur = g.db.execute('select title,text,img_name, date, creator from entries where id == ?', [id])
	
	entries = [dict(title=row[0],text=row[1],img_name=row[2], date=row[3], creator=row[4]) for row in cur.fetchall()]
	if entries[0]['img_name'] != "":
		im = Image.open('img/'+entries[0]['img_name'])
		entries[0]['img_size'] = im.size
	print entries
	return render_template('entry.html', entry=entries[0])
	
#editing a specific entry
@app.route('/edit/<id>')
def edit(id):
	if session['logged_in'] == False:
		return redirect(url_for('home'))		

	cur = g.db.execute('select title,text,id,date, creator from entries where id == ?', [id])
	entries = [dict(title=row[0],text=row[1], id=row[2], date=row[3], creator=row[4]) for row in cur.fetchall()]

	if entries[0]['creator'] != session['username']:
		return redirect(url_for('home'))
# 	if entries[0]['img_name'] != "":
# 		im = Image.open('img/'+entries[0]['img_name'])
# 		entries[0]['img_size'] = im.size
	print entries
	return render_template('edit.html', entry=entries[0])
	
#uploading file	
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)
#logs out
@app.route('/log_out')
def log_out():
	session['logged_in'] = False
	return redirect(url_for("home"))	

if __name__ == '__main__':
	app.run()