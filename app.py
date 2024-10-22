from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://flaskuser:password@localhost/flask_todo'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'password'  # Cambia esta clave secreta

db = SQLAlchemy(app)
jwt = JWTManager(app)

# Modelo de usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Modelo de publicación
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Crear tablas
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return jsonify({"message": "API está funcionando"}), 200

# Ruta de registro de usuario
@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"message": "Usuario o contraseña no proporcionados"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Usuario creado exitosamente"}), 201
    except:
        return jsonify({"message": "El usuario ya existe"}), 400

# Ruta de inicio de sesión
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Credenciales incorrectas"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200

# Crear una nueva publicación
@app.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    title = request.json.get('title')
    content = request.json.get('content')
    user_id = get_jwt_identity()

    if not title or not content:
        return jsonify({"message": "Título y contenido son necesarios"}), 400

    new_post = Post(title=title, content=content, user_id=user_id)
    db.session.add(new_post)
    db.session.commit()

    return jsonify({"message": "Publicación creada exitosamente"}), 201

# Obtener todas las publicaciones
@app.route('/posts', methods=['GET'])
def get_posts():
    posts = Post.query.all()

    return jsonify([{
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "user_id": post.user_id
    } for post in posts]), 200

# Actualizar una publicación
@app.route('/posts/<int:id>', methods=['PUT'])
@jwt_required()
def update_post(id):
    post = Post.query.get_or_404(id)
    user_id = get_jwt_identity()

    if post.user_id != user_id:
        return jsonify({"message": "No autorizado"}), 403

    post.title = request.json.get('title', post.title)
    post.content = request.json.get('content', post.content)

    db.session.commit()

    return jsonify({"message": "Publicación actualizada"}), 200

# Eliminar una publicación
@app.route('/posts/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_post(id):
    post = Post.query.get_or_404(id)
    user_id = get_jwt_identity()

    if post.user_id != user_id:
        return jsonify({"message": "No autorizado"}), 403

    db.session.delete(post)
    db.session.commit()

    return jsonify({"message": "Publicación eliminada"}), 200

if __name__ == '__main__':
    app.run()
