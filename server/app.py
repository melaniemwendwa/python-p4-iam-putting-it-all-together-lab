from flask import request, session, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe


# ------------------------
# SIGNUP
# ------------------------
class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")
        image_url = data.get("image_url")
        bio = data.get("bio")

        try:
            # create new user
            new_user = User(
                username=username,
                image_url=image_url,
                bio=bio
            )
            if password:
                new_user.password_hash = password

            db.session.add(new_user)
            db.session.commit()

            # store user id in session
            session["user_id"] = new_user.id

            return {
                "id": new_user.id,
                "username": new_user.username,
                "image_url": new_user.image_url,
                "bio": new_user.bio
            }, 201

        except IntegrityError:
            db.session.rollback()
            return {"errors": ["Username already taken."]}, 422
        except ValueError as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 422


# ------------------------
# CHECK SESSION
# ------------------------
class CheckSession(Resource):
    def get(self):
        user_id = session.get("user_id")

        if not user_id:
            return {"error": "Unauthorized"}, 401

        user = db.session.get(User, user_id)
        if not user:
            return {"error": "Unauthorized"}, 401

        return {
            "id": user.id,
            "username": user.username,
            "image_url": user.image_url,
            "bio": user.bio
        }, 200


# ------------------------
# LOGIN
# ------------------------
class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session["user_id"] = user.id
            return {
                "id": user.id,
                "username": user.username,
                "image_url": user.image_url,
                "bio": user.bio
            }, 200

        return {"error": "Invalid username or password"}, 401


# ------------------------
# LOGOUT
# ------------------------
class Logout(Resource):
    def delete(self):
        user_id = session.get("user_id")

        if not user_id:  # catches missing or None
            return {"error": "Unauthorized"}, 401

        session.pop("user_id", None)
        return {}, 204


# ------------------------
# RECIPES
# ------------------------
class RecipeIndex(Resource):
    def get(self):
        user_id = session.get("user_id")
        if not user_id:
            return {"error": "Unauthorized"}, 401

        recipes = Recipe.query.all()
        response = []
        for r in recipes:
            response.append({
                "id": r.id,
                "title": r.title,
                "instructions": r.instructions,
                "minutes_to_complete": r.minutes_to_complete,
                "user": {
                    "id": r.user.id,
                    "username": r.user.username,
                    "image_url": r.user.image_url,
                    "bio": r.user.bio
                }
            })
        return response, 200

    def post(self):
        user_id = session.get("user_id")
        if not user_id:
            return {"error": "Unauthorized"}, 401

        data = request.get_json()
        title = data.get("title")
        instructions = data.get("instructions")
        minutes_to_complete = data.get("minutes_to_complete")

        try:
            new_recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=user_id
            )
            db.session.add(new_recipe)
            db.session.commit()

            return {
                "id": new_recipe.id,
                "title": new_recipe.title,
                "instructions": new_recipe.instructions,
                "minutes_to_complete": new_recipe.minutes_to_complete,
                "user": {
                    "id": new_recipe.user.id,
                    "username": new_recipe.user.username,
                    "image_url": new_recipe.user.image_url,
                    "bio": new_recipe.user.bio
                }
            }, 201

        except ValueError as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 422


# Register resources
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)