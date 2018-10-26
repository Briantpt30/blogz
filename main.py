from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:blogz@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B' 

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(500))
    owner_id = db.Column(db.String(500), db.ForeignKey('user.username'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)


@app.before_request
def require_login():
    allowed_routes = ['all_blogs', 'login', 'signup', 'blog','index','static']
    if request.endpoint not in allowed_routes and 'user' not in session:
        return redirect('/login')


@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)



@app.route('/all')
def all_blogs():
    blogs = Blog.query.paginate(None, 5, True) 
    return render_template('blog.html',blogs=blogs)




@app.route('/blog', methods=['POST', 'GET'])
def blog():
    blog_id = request.args.get('id')
    user_id = request.args.get('user')

    if blog_id is not None:
        blogs = Blog.query.filter_by(id=blog_id)
        return render_template('blogpost.html', blogs=blogs)

    elif user_id is not None:
        blogs = Blog.query.filter_by(owner_id=user_id)
        return render_template('singleuser.html',blogs=blogs)

    


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_pw_hash(password, user.pw_hash):
            session['user'] = username
            flash("Logged in")
            return redirect('/newpost')
        else:
           flash('User password incorrect, or user does not exist', 'error')


    return render_template('login.html')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        if valid_text_length(username) == False or no_spaces(username) == False:
            flash("That's not a valid username", 'error')
        if valid_text_length(password) == False or no_spaces(password) == False:
            flash("That's not a valid password", 'error')
        if verify_pw(password, verify) == False:
            flash("Passwords don't match", 'error')
        if empty_entry(username) == False or empty_entry(password) == False or empty_entry(verify) == False:
            flash('One or more fields are invalid', 'error')

        exsisting_user = User.query.filter_by(username=username).first()
        if not exsisting_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['user'] = username
            return redirect('/newpost')
        else:
            return flash("A user with that username already exists")    


    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/blog')


def valid_text_length(text):
    if len(text) > 3 and len(text) < 20:
        return True
    else:
        return False  

def no_spaces(text):
    if ' ' in text:
        return False
    else:
        return True

def verify_pw(pw, verify):
    if verify == pw:
        return True
    else:
        return False    

def verify_email(email):
    if '@' in email and '.' in email:
        return True
    else:
        return False    

def empty_entry(entry):
    if entry == '':
        return False
    else:
        return True




@app.route('/newpost', methods=['POST'])
def newpost_error():
    body_error = ''
    title_error = ''
    blog_body = request.form['blog']
    blog_title = request.form['title']
    spider_man = True
    owner = User.query.filter_by(username=session['user']).first()
    if empty_entry(blog_body) == False:
        body_error = 'Please fill in body'
        spider_man = False
    if empty_entry(blog_title) == False:
        title_error ='Please fill in title'
        spider_man = False


    if spider_man == False:
        return render_template('newpost.html', title_error=title_error, body_error=body_error)    
    else:
        blog_body = request.form['blog']
        blog_title = request.form['title']
        new_blog = Blog(blog_title, blog_body, owner)
        db.session.add(new_blog)
        db.session.commit()
        return redirect(f'/blog?id={new_blog.id}&user={owner.username}')




@app.route('/newpost', methods=['GET'])
def newpost():
        return render_template('newpost.html')


if __name__ == '__main__':
    app.run()