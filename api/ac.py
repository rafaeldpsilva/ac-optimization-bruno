import sys
sys.path.append('.')

from core.ACOptimization import ACOptimization

if __name__ == "__main__":
    cr = ACOptimization()
    #cr.daemon = True
    cr.start()
    cr.join()