from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)
    
class Homelab(Resource):
    def post(self):
        return {'message':'Bem Vindo ao homelab'}
    
    def get(self, name):
        return {'message':'Services'}

api.add_resource(Homelab, '/homelab' , '/homelab/<string:name>')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
