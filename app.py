from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)
    
class Distros(Resource):
    def post(self):
        return {'message':'Distros Linux'}
    
    def get(self, name):
        return {'Distro':'Name'}

api.add_resource(Distros, '/distros' , '/distros/<string:name>')

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
