from flask import Flask
from flask_restplus import Api, Resource, fields, reqparse
import h5pyd

app = Flask(__name__)
api = Api(app)

domain = 'testfile.testdir.testh5serv.org'
endpoint = 'http://54.167.16.161:5000'
f = h5pyd.File(domain, 'r', endpoint)

@api.route('/path/<path:dsetname>')
class HDF5Path(Resource):
  # Note: enter without leading slash
  def get(self, dsetname):
    try:
      pth = f[dsetname]
    except:
      return { 'dataset' : 'not-found' }
    if (type(pth) == h5pyd._hl.group.Group): 
      tree = []
      pth.visit(lambda x: tree.append(x))
      return { 'group' : pth.name , 'uuid' : pth.id.uuid , 'contents' : tree }
    elif (type(pth) == h5pyd._hl.dataset.Dataset):
      return { 'dataset' : pth.name , 'uuid' : pth.id.uuid, 
               'shape' : pth.shape, 'dtype' : pth.dtype.name }

parser = reqparse.RequestParser()
parser.add_argument('path')
parser.add_argument('elements')

# Question:
# What can be passed to '[' function in h5pyd? numpy arrays? How does d[0:10, 0:10, 0:10] work,
#   and why doesn't it work here?

@api.route('/data')
class HDF5Data(Resource):
  @api.expect(parser)
  def get(self):
    args = parser.parse_args()
    try:
      p = args['path']
      pth = f[p] 
      E = args['elements'].split(',')      # E is an array of string
      if (len(pth.shape) == 3):            # generalize to arbitrary dimension
        res = pth[int(E[0]), int(E[1]), int(E[2])]
      elif (len(pth.shape) == 2):
        res = pth[int(E[0]), int(E[1])]
      elif (len(pth.shape) == 1):
        res = pth[int(E[0])]
      print("Result = %s" % res)
    except:
      return { 'result' : 'error' }
    return { 'path' : args['path'], 'elements' : args['elements'] , 'output' : str(res) } 


if __name__ == '__main__':
  app.run(debug=True)



