from flask import Flask
from flask_restplus import Api, Resource, fields, reqparse
import h5pyd

app = Flask(__name__)
api = Api(app)

domain = 'testfile.testdir.testh5serv.org'
endpoint = 'http://107.23.2.183:5000'       # Note: need to change this every time test server is relaunched
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
# Answer: indices are of type numpy.slice
#   0:10:1 is shorthand for slice(0, 10, 1)
#   expect 'elements' to be a comma-separated string of the form start:stop:step
# E.g., elements: 0:4:2,0:3:1,0:6:3

@api.route('/data')
class HDF5Data(Resource):
  @api.expect(parser)
  def get(self):
    args = parser.parse_args()
    try:
      p = args['path']
      pth = f[p] 
      E = args['elements'].split(',')      # E is an array of string
      slices = []

      for ee in E:
        (s0, s1, s2) = ee.split(':')
        slices.append(slice(int(s0), int(s1), int(s2)))

      if (len(slices) == len(pth.shape)):
        if (len(pth.shape) == 3):            # generalize to arbitrary dimension
          res = pth[slices[0], slices[1], slices[2]]
        elif (len(pth.shape) == 2):
          res = pth[slices[0], slices[1]]
        elif (len(pth.shape) == 1):
          res = pth[slices[0]] 
        else:
          raise ValueError('Bad slice')
      else:
        raise ValueError('Bad slice')
      
    except ValueError as err:
      return { 'result' : 'slice-syntax-error' }
    return { 'path' : args['path'], 'elements' : args['elements'] , 'output' : str(res) } 


if __name__ == '__main__':
  app.run(debug=True)



