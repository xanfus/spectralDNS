from spectralDNS import config, get_solver
from numpy import array, sum, pi, sin, cos, float64
import sys

def initialize(**kw):
    if config.params.solver == 'NS':
        initialize1(**kw)
    
    else:
        initialize2(**kw)
        
def initialize1(U, U_hat, X, FFT, **kw):    
    U[0] = sin(X[0])*cos(X[1])*cos(X[2])
    U[1] =-cos(X[0])*sin(X[1])*cos(X[2])
    U[2] = 0 
    for i in range(3):
        U_hat[i] = FFT.fftn(U[i], U_hat[i])
        
def initialize2(U, W_hat, X, FFT, work, cross2, K, **kw):
    U[0] = sin(X[0])*cos(X[1])*cos(X[2])
    U[1] =-cos(X[0])*sin(X[1])*cos(X[2])
    U[2] = 0         
    F_tmp = work[(W_hat, 0)]
    for i in range(3):
        F_tmp[i] = FFT.fftn(U[i], F_tmp[i])
    W_hat = cross2(W_hat, K, F_tmp)

def regression_test(comm, U_hat, U, curl, rank, Curl, FFT, params, K,
                    backward_velocity, work, **kw):
    dx, L = params.dx, params.L
    U = backward_velocity()
    if params.solver == 'NS':
        curl = Curl(U_hat, curl, work, FFT, K)
    elif params.solver == 'VV':
        for i in range(3):
            curl[i] = FFT.ifftn(kw['W_hat'][i], curl[i])
    vol = dx[0]*dx[1]*dx[2]/L[0]/L[1]/L[2]/2
    w = comm.reduce(sum(curl.astype(float64)*curl.astype(float64))*vol)
    k = comm.reduce(sum(U.astype(float64)*U.astype(float64))*vol) # Compute energy with double precision
    if rank == 0:
        print k
        assert round(k - 0.124953117517, params.ntol) == 0
        assert round(w - 0.375249930801, params.ntol) == 0

if __name__ == "__main__":
    config.update(
        {
        'nu': 0.000625,             # Viscosity
        'dt': 0.01,                 # Time step
        'T': 0.1,                   # End time
        'L': [2*pi, 2*pi, 2*pi],
        'M': [4, 4, 4]
        }
    )
    solver = get_solver(regression_test=regression_test)    
    initialize(**vars(solver))
    solver.solve()
    
    config.params.dealias = '3/2-rule'
    initialize(**vars(solver))
    solver.solve()
    
    config.params.dealias = '2/3-rule'
    config.params.optimization = 'cython'
    config.params.make_profile = 1
    initialize(**vars(solver))
    solver.solve()    
    
    config.params.write_result = 1
    config.params.checkpoint = 1
    config.dt = 0.01
    config.T = 0.04
    solver.regression_test = lambda **kwargs: None
    solver.solve()
    
    VVsolver = get_solver(regression_test=regression_test, 
                          parse_args=sys.argv[1:-1]+['VV'])    
    initialize(**vars(VVsolver))
    VVsolver.solve()

    config.params.make_profile = 1
    config.params.dealias = '3/2-rule'
    initialize(**vars(VVsolver))
    VVsolver.solve()
    
    config.params.dealias = '2/3-rule'
    config.params.optimization = 'cython'
    initialize(**vars(VVsolver))
    VVsolver.solve()    

    config.params.write_result = 1
    config.params.checkpoint = 1
    config.dt = 0.01
    config.T = 0.04
    VVsolver.regression_test = lambda **kwargs: None
    VVsolver.solve()    
