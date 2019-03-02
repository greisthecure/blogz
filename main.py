from flask import Flask, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:Playstation1@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'itsasecret'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(500))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30),unique=True)
    password = db.Column(db.String(15))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

@app.before_request
def require_login():  # Only allows viewer (not logged in) to see certain pages only
    allowed_routes = ['login', 'register', 'index', 'blog']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/index', methods=['GET'])
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/login', methods=['POST', 'GET'])
def login():

    username_error = ""
    pass_error = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.password == password: # searches for the username in the database
            session['username'] = username # stores the username in the session
            return redirect('/newpost')
        
        if not user:
            username_error = "Username does not exist"

        if user and user.password != password:
            pass_error = "Password is incorrect"

    return render_template('login.html', username_error=username_error, pass_error=pass_error)

@app.route('/register', methods=['POST', 'GET'])
def register():

    username_error = ""
    pass_error = ""
    verifypw_error = ""
    username = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        # validation tests go here!
        if username == "":
            username_error = "Please enter a Username"

        if len(username) < 3 or len(username) > 20:
            username_error = "Username length must be > 3 and < 20"

        for char in username:
            if char == " ":
                username_error = "No spaces allowed in Username"
            else:
                existing_user = User.query.filter_by(username=username).first()
                if existing_user:
                    username_error = "Username already exists, please choose another username"

    # password validation tests
        if password == "":
            pass_error = "Please enter a password"
            print(pass_error)

        if " " in password:
            pass_error = "Passwords cannot have spaces"
            print(pass_error)

        if len(password) < 3 or len(password) > 20:
            pass_error = "Password length must be > 3 and < 20 characters"
            print(pass_error)

    # password verify field MUST match password field
        if verify != password:
            verifypw_error = "Password entries do not match, Please re-enter your password"
            print(verifypw_error)
            verify = ""

        if not username_error and not pass_error and not verifypw_error:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')

    return render_template("register.html", username=username, username_error=username_error, pass_error=pass_error, verifypw_error=verifypw_error)

@app.route('/newpost', methods=['POST', 'GET'])
def add_post(): # adds the post to the database, new post acceptance then redirects to that blog post's individual entry page

    owner = User.query.filter_by(username=session['username']).first()
    

    title = ""
    body = ""
    title_error = ""
    post_error = ""
    

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        if len(title) == 0:
            title_error = "Please enter a title for your post"   

        if len(body) == 0:
            post_error = "Please enter your blog post here"

        if title_error or post_error: # renders the form with either or both errors
            return render_template('newpost.html', title=title, title_error=title_error, body=body, post_error=post_error)

        if not title_error and not post_error:
            new_post = Blog(title, body, owner)
            db.session.add(new_post)
            db.session.commit()
            entry = new_post.id
            return render_template('displaypost.html', title=new_post.title, body=new_post.body, owner=new_post.owner)

    return render_template('newpost.html', title=title, body=body, title_error=title_error, post_error=post_error)

# display all blog posts on the main page
@app.route('/blog', methods=['POST', 'GET'])
def blog():

    id = request.args.get("id")
    user_id = request.args.get("user")
    
    if not id and not user_id:
        entries = Blog.query.order_by(Blog.id.desc()).all()
        return render_template('blog.html', entries=entries)

    if not user_id: # displays single blog post
        entries = Blog.query.filter_by(id=id).first()
        owner_id = entries.owner_id
        title = entry.title
        body = entry.body
        username = entry.owner.username
        return redirect("displaypost.html", title=title, body=body, username=username, owner_id=owner_id, entry=entry)
    else:
        owner = User.query.filter_by(id=user_id).first()
        entries = Blog.query.filter_by(owner=owner).order_by(Blog.id.desc()).all()
        return render_template("blog.html", title=owner.username, entries=entries, user=user_id)

# displays the single post on a separate page
@app.route('/displaypost', methods=['GET'])
def displaypost():

    id = request.args.get("id")
    entry = Blog.query.filter_by(id=id).first()
    
    return render_template('displaypost.html', title=entry.title, body=entry.body, owner_id=entry.owner_id, username=entry.owner.username)

@app.route('/logout') # logs the user out of the site redirects to index
def logout():
    del session['username']
    return redirect('/index')


if __name__=='__main__':
    app.run()