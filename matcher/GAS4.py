import pandas as pd
from matcher import Matcher
from core import GraphSet
import docplex.mp.model as cpx
from sklearn.metrics.pairwise import pairwise_distances

# Docplex brute-force approach

# GAS4 is extremely similar to GAS. It is indeed rewritten, using smarter ways.
# For instance, variables are declared all in one push, through the right structure.

class GAS4(Matcher):

    def __init__(self,X=None,Y=None,f=None):
        Matcher.__init__(self,X,Y,f)
        self.name="Gaaaaaaas!"
        
    
    # The match function: this function find the best match among the equivalent classes
    def match(self,X,Y):
        # Take the two graphs - they have already the same size
        self.X=X
        self.Y=Y
        
        nX=self.X.nodes()
        set_I = range(nX)
        
        # building up the matrix of pairwise distances:

        # GAS V0 - not working properly, if null edges are not defined (to 0.0)
#        gas = pd.DataFrame(pairwise_distances(X.to_vector_with_attributes().transpose(),
#                                              Y.to_vector_with_attributes().transpose()),
#                           columns = Y.to_vector_with_attributes().columns,
#                           index = X.to_vector_with_attributes().columns)

        
        # GAS V1 
        # Create Graph set:
        GG = GraphSet()
        GG.add(self.X)
        GG.add(self.Y)
        gg_mat = GG.to_matrix_with_attr()
        gas = pd.DataFrame(pairwise_distances(gg_mat.iloc[[0]].transpose(),
                                              gg_mat.iloc[[1]].transpose()),
                           columns = gg_mat.iloc[[1]].columns,
                           index = gg_mat.iloc[[0]].columns)
        del GG, gg_mat
        
               
        # optimization model:
        # initialize the model
        opt_model = cpx.Model(name="HP Model", ignore_names=True, checker='off')

        # list of binary variables: 1 if i match j, 0 otherwise
        # x_vars is n x n x n x n
        x_vars  = opt_model.binary_var_matrix(set_I, set_I, name="x")
        
        # constraints - imposing that there is a one to one correspondence between the nodes in the two networks
        opt_model.add_constraints( (opt_model.sum(x_vars[i,u] for i in set_I)== 1 for u in set_I),
                                  ("constraint_r{0}".format(u) for u in set_I) )

        opt_model.add_constraints( (opt_model.sum(x_vars[i,u] for u in set_I)== 1 for i in set_I), 
                                  ("constraint_c{0}".format(i) for i in set_I)  )
        
        
        # objective function - sum the distance between nodes and the distance between edges
        # e.g. (i,i) is a node in X, (u,u) is a node in Y, (i,j) is an edge in X, (u,v) is an edge in Y.

        objective = opt_model.sum(x_vars[i,u] * gas.loc['({0}, {0})'.format(i), '({0}, {0})'.format(u)]
                                  for i in set_I 
                                  for u in set_I) + opt_model.sum(x_vars[i,u] * x_vars[j,v] * gas.loc['({0}, {1})'.format(i,j), 
                                                                                                      '({0}, {1})'.format(u,v)]
                                                                  for i in set_I 
                                                                  for u in set_I
                                                                  for j in set_I if j != i
                                                                  for v in set_I if v != u)

        
        # Minimizing the distances as specified in the objective function
        opt_model.minimize(objective)
        # Finding the minimum
        opt_model.solve()

        # Save in f the permutation: <3
        ff = {k:v.solution_value for k, v in x_vars.items()}
        self.f = [k for (j,k), v in ff.items() if v == 1]

        
        del gas

        # <3
 
            

